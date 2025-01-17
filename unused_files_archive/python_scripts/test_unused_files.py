import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Set
import time
import re
import ast

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_unused_files.log'),
        logging.StreamHandler()
    ]
)

class TemplateUsageVisitor(ast.NodeVisitor):
    """AST Visitor zur Erkennung von Template-Verwendungen in Python-Code"""
    def __init__(self):
        self.templates = set()
        
    def visit_Call(self, node):
        # Suche nach render_template Aufrufen
        if isinstance(node.func, ast.Name) and node.func.id == 'render_template':
            if node.args and isinstance(node.args[0], ast.Str):
                self.templates.add(node.args[0].s)
        # Suche nach render_template_string Aufrufen
        elif isinstance(node.func, ast.Name) and node.func.id == 'render_template_string':
            if node.args and isinstance(node.args[0], ast.Str):
                self.templates.add(node.args[0].s)
        self.generic_visit(node)

class UnusedFileTester:
    def __init__(self):
        self.workspace_root = os.getcwd()
        self.test_dir = os.path.join(self.workspace_root, 'test_unused_files')
        self.results: Dict[str, Dict] = {}
        self.used_templates: Set[str] = set()
        self.template_inheritance_map: Dict[str, Set[str]] = {}
        
    def analyze_template_usage(self):
        """Analysiert die Verwendung von Templates in Python-Dateien und Template-Vererbung"""
        print("\nAnalysiere Template-Verwendung...")
        
        # Analysiere Python-Dateien nach Template-Verwendungen
        for root, _, files in os.walk(self.workspace_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            tree = ast.parse(f.read())
                            visitor = TemplateUsageVisitor()
                            visitor.visit(tree)
                            self.used_templates.update(visitor.templates)
                            if visitor.templates:
                                logging.info(f"Templates gefunden in {file_path}: {visitor.templates}")
                    except Exception as e:
                        logging.warning(f"Fehler beim Analysieren von {file_path}: {str(e)}")
        
        # Analysiere Template-Vererbung
        template_dir = os.path.join(self.workspace_root, 'app', 'templates')
        if os.path.exists(template_dir):
            for root, _, files in os.walk(template_dir):
                for file in files:
                    if file.endswith('.html'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            # Finde extends und include Anweisungen
                            rel_path = os.path.relpath(file_path, template_dir)
                            self.template_inheritance_map[rel_path] = set()
                            
                            # Suche nach extends
                            extends_matches = re.findall(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"]', content)
                            self.template_inheritance_map[rel_path].update(extends_matches)
                            
                            # Suche nach includes
                            include_matches = re.findall(r'{%\s*include\s+[\'"]([^\'"]+)[\'"]', content)
                            self.template_inheritance_map[rel_path].update(include_matches)
                            
                            # Wenn dieses Template andere einbindet, markiere es als verwendet
                            if extends_matches or include_matches:
                                logging.info(f"Template-Abhängigkeiten in {rel_path}: {extends_matches + include_matches}")
                                
                        except Exception as e:
                            logging.warning(f"Fehler beim Analysieren von Template {file_path}: {str(e)}")
        
        # Erweitere verwendete Templates um abhängige Templates
        templates_to_check = self.used_templates.copy()
        checked_templates = set()
        
        while templates_to_check:
            template = templates_to_check.pop()
            if template in checked_templates:
                continue
                
            checked_templates.add(template)
            
            # Füge abhängige Templates hinzu
            if template in self.template_inheritance_map:
                dependencies = self.template_inheritance_map[template]
                templates_to_check.update(dependencies)
                self.used_templates.update(dependencies)
        
        print(f"Gefundene verwendete Templates: {len(self.used_templates)}")
        for template in sorted(self.used_templates):
            print(f"- {template}")
        
    def setup_test_directory(self):
        """Erstellt das Test-Verzeichnis"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        logging.info(f"Test-Verzeichnis erstellt: {self.test_dir}")
    
    def load_latest_report(self) -> Dict:
        """Lädt den neuesten Analysebericht"""
        reports = [f for f in os.listdir() if f.startswith('unused_files_report_') and f.endswith('.json')]
        if not reports:
            raise FileNotFoundError("Kein Analysebericht gefunden!")
        latest_report = max(reports)
        with open(latest_report, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def move_file(self, file_path: str) -> str:
        """Verschiebt eine einzelne Datei ins Test-Verzeichnis"""
        if os.path.exists(file_path):
            rel_path = os.path.relpath(file_path, self.workspace_root)
            target_path = os.path.join(self.test_dir, rel_path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.move(file_path, target_path)
            logging.info(f"Datei verschoben: {rel_path}")
            return rel_path
        return ""
    
    def restore_file(self, rel_path: str) -> None:
        """Stellt eine einzelne Datei wieder her"""
        source_path = os.path.join(self.test_dir, rel_path)
        target_path = os.path.join(self.workspace_root, rel_path)
        if os.path.exists(source_path):
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.move(source_path, target_path)
            logging.info(f"Datei wiederhergestellt: {rel_path}")
    
    def test_app(self) -> Dict[str, bool]:
        """Testet die App durch Starten des Servers und grundlegende Checks"""
        results = {}
        try:
            # Starte den Server im Hintergrund
            server_process = subprocess.Popen(
                ['python', 'server.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Warte kurz, bis der Server gestartet ist
            time.sleep(5)
            
            # Teste grundlegende Funktionalität mit curl
            test_routes = [
                '/',
                '/tools',
                '/workers',
                '/consumables',
                '/tickets',
                '/admin/dashboard',  # Admin-Bereich
                '/auth/login'        # Auth-Bereich
            ]
            
            for route in test_routes:
                try:
                    result = subprocess.run(
                        ['curl', '-s', '-L', '-o', '/dev/null', '-w', '%{http_code}', f'http://localhost:5000{route}'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    status_code = int(result.stdout)
                    results[route] = 200 <= status_code < 400
                    logging.info(f"Route {route} getestet (Status: {status_code})")
                except subprocess.TimeoutExpired:
                    results[route] = False
                    logging.error(f"Timeout bei Route {route}")
                except Exception as e:
                    results[route] = False
                    logging.error(f"Fehler bei Route {route}: {str(e)}")
            
        except Exception as e:
            logging.error(f"Fehler beim Testen der App: {str(e)}")
            return {route: False for route in test_routes}
        finally:
            # Server beenden
            server_process.terminate()
            server_process.wait()
            
        return results
    
    def test_single_file(self, file_path: str) -> Dict:
        """Testet die App ohne eine einzelne Datei"""
        rel_path = os.path.relpath(file_path, self.workspace_root)
        file_type = self.get_file_type(rel_path)
        
        # Überprüfe Templates vor dem Test
        if file_type == 'template':
            template_path = os.path.relpath(file_path, os.path.join(self.workspace_root, 'app', 'templates'))
            if template_path in self.used_templates:
                print("✗ Template wird verwendet!")
                result = {
                    'file': rel_path,
                    'type': file_type,
                    'is_safe_to_remove': False,
                    'reason': 'Template wird aktiv verwendet'
                }
                self.results[rel_path] = result
                return result
        
        print(f"\nTeste Datei: {rel_path}")
        print(f"Typ: {file_type}")
        
        # Originale Routen-Ergebnisse speichern
        if not hasattr(self, 'original_results'):
            print("Teste App im Originalzustand...")
            self.original_results = self.test_app()
        
        # Verschiebe Datei
        moved_path = self.move_file(file_path)
        if not moved_path:
            return {'status': 'error', 'message': 'Datei konnte nicht verschoben werden'}
        
        # Teste App
        test_results = self.test_app()
        
        # Vergleiche Ergebnisse
        changes = {}
        for route, success in test_results.items():
            if success != self.original_results[route]:
                changes[route] = {
                    'original': self.original_results[route],
                    'without_file': success
                }
        
        # Stelle Datei wieder her
        self.restore_file(moved_path)
        
        result = {
            'file': rel_path,
            'type': file_type,
            'is_safe_to_remove': len(changes) == 0,
            'affected_routes': changes
        }
        
        # Speichere Ergebnis
        self.results[rel_path] = result
        
        # Zeige Zusammenfassung
        if result['is_safe_to_remove']:
            print("✓ Datei kann sicher entfernt werden")
        else:
            print("✗ Datei wird benötigt")
            for route, change in changes.items():
                print(f"  - Route {route} betroffen")
        
        return result
    
    def get_file_type(self, file_path: str) -> str:
        """Bestimmt den Dateityp basierend auf Pfad und Erweiterung"""
        if '/templates/' in file_path:
            return 'template'
        elif '/static/' in file_path:
            return 'static'
        elif file_path.endswith('.py'):
            return 'python'
        elif file_path.endswith('.db'):
            return 'database'
        elif file_path.endswith('.sql'):
            return 'database_migration'
        elif file_path.endswith('.json'):
            return 'configuration'
        elif file_path.endswith(('.md', '.txt')):
            return 'documentation'
        else:
            return 'other'
    
    def save_results(self):
        """Speichert die Testergebnisse in einer JSON-Datei"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"file_test_results_{timestamp}.json"
        
        # Gruppiere Ergebnisse nach Typ
        grouped_results = {}
        for file_path, result in self.results.items():
            file_type = result['type']
            if file_type not in grouped_results:
                grouped_results[file_type] = []
            grouped_results[file_type].append(result)
        
        # Erstelle Zusammenfassung
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files_tested': len(self.results),
            'safe_to_remove': len([r for r in self.results.values() if r['is_safe_to_remove']]),
            'needed_files': len([r for r in self.results.values() if not r['is_safe_to_remove']]),
            'results_by_type': grouped_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\nDetaillierten Bericht gespeichert in: {filename}")
    
    def run_test_sequence(self):
        """Führt die komplette Testsequenz aus"""
        try:
            self.setup_test_directory()
            report = self.load_latest_report()
            
            print("\n=== Starte detaillierte Dateianalyse ===")
            
            # Analysiere Template-Verwendung zuerst
            self.analyze_template_usage()
            
            # Sammle alle Dateien aus dem Report
            all_files = []
            for category in report['unused_by_type']:
                all_files.extend(report['unused_by_type'][category])
            
            total_files = len(all_files)
            print(f"\nGefundene Dateien zum Testen: {total_files}")
            
            # Teste jede Datei einzeln
            for i, file_path in enumerate(all_files, 1):
                print(f"\nTeste Datei {i}/{total_files}")
                self.test_single_file(file_path)
            
            # Speichere Ergebnisse
            self.save_results()
            
            # Zeige Zusammenfassung
            safe_files = [f for f, r in self.results.items() if r['is_safe_to_remove']]
            needed_files = [f for f, r in self.results.items() if not r['is_safe_to_remove']]
            
            print("\n=== Analyse abgeschlossen ===")
            print(f"Getestete Dateien: {len(self.results)}")
            print(f"Sicher zu entfernende Dateien: {len(safe_files)}")
            print(f"Benötigte Dateien: {len(needed_files)}")
            
        except Exception as e:
            logging.error(f"Fehler während der Testsequenz: {str(e)}")
            print(f"\nFehler: {str(e)}")

def main():
    tester = UnusedFileTester()
    tester.run_test_sequence()

if __name__ == '__main__':
    main() 