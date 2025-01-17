import os
from datetime import datetime
import sys
import logging
from pathlib import Path
import shutil
import json
import ast
import importlib
import pkgutil
import re
from typing import Set, Dict, List

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unused_files.log'),
        logging.StreamHandler()
    ]
)

class FileAnalyzer:
    def __init__(self):
        self.workspace_root = os.getcwd()
        self.ignored_patterns = [
            '__pycache__', 
            'venv', 
            '.git', 
            'node_modules',
            'backups',
            'flask_session',
            'uploads',
            '.pytest_cache',
            '.coverage'
        ]
        self.ignored_extensions = {'.pyc', '.pyo', '.pyd', '.log', '.bak', '.git', '.DS_Store'}
        self.known_routes: Set[str] = set()
        self.template_files: Set[str] = set()
        self.static_files: Set[str] = set()
        
    def create_backup(self, file_path: str) -> None:
        """Erstellt ein Backup einer Datei"""
        backup_dir = os.path.join(self.workspace_root, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(
            backup_dir, 
            f"{os.path.basename(file_path)}_{timestamp}.bak"
        )
        shutil.copy2(file_path, backup_path)
        logging.info(f"Backup erstellt: {backup_path}")

    def find_python_imports(self, file_path: str) -> Set[str]:
        """Analysiert Python-Dateien auf Imports und verwendete Module"""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Direkte Imports
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name.split('.')[0])
                # From Imports
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
                # Template-Referenzen in Strings
                elif isinstance(node, ast.Str):
                    if node.s.endswith('.html'):
                        self.template_files.add(node.s)
                    elif node.s.startswith('static/'):
                        self.static_files.add(node.s)
                
        except Exception as e:
            logging.warning(f"Fehler beim Analysieren von {file_path}: {str(e)}")
        
        return imports

    def find_flask_routes(self, file_path: str) -> None:
        """Findet Flask-Routen in Python-Dateien"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Suche nach Route-Dekoratoren
            route_patterns = [
                r'@\w+\.route\([\'"]([^\'"]+)[\'"]',  # Standard Flask-Routen
                r'@\w+\.get\([\'"]([^\'"]+)[\'"]',    # HTTP GET
                r'@\w+\.post\([\'"]([^\'"]+)[\'"]',   # HTTP POST
                r'@\w+\.put\([\'"]([^\'"]+)[\'"]',    # HTTP PUT
                r'@\w+\.delete\([\'"]([^\'"]+)[\'"]'  # HTTP DELETE
            ]
            
            for pattern in route_patterns:
                routes = re.findall(pattern, content)
                self.known_routes.update(routes)
                
        except Exception as e:
            logging.warning(f"Fehler beim Suchen von Routen in {file_path}: {str(e)}")

    def analyze_template_dependencies(self, template_dir: str) -> Set[str]:
        """Analysiert Template-Abhängigkeiten"""
        template_deps = set()
        
        for root, _, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Suche nach Template-Erweiterungen und Includes
                        extends = re.findall(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"]', content)
                        includes = re.findall(r'{%\s*include\s+[\'"]([^\'"]+)[\'"]', content)
                        
                        template_deps.update(extends)
                        template_deps.update(includes)
                        
                        # Suche nach statischen Dateien
                        static_files = re.findall(r'url_for\s*\(\s*[\'"]static[\'"]\s*,\s*filename\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                        self.static_files.update(static_files)
                        
                    except Exception as e:
                        logging.warning(f"Fehler beim Analysieren von Template {file_path}: {str(e)}")
        
        return template_deps

    def find_used_files(self) -> Set[str]:
        """Findet alle genutzten Dateien durch statische Analyse"""
        used_files = set()
        python_files = set()
        
        # Finde alle Python-Dateien
        for root, _, files in os.walk(self.workspace_root):
            if any(ignore in root for ignore in self.ignored_patterns):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.add(file_path)
                    used_files.add(file_path)  # Python-Dateien sind per Definition genutzt
                    
                    # Analysiere Imports und Routen
                    self.find_python_imports(file_path)
                    self.find_flask_routes(file_path)
        
        # Analysiere Templates
        template_dir = os.path.join(self.workspace_root, 'app', 'templates')
        if os.path.exists(template_dir):
            template_deps = self.analyze_template_dependencies(template_dir)
            
            # Füge gefundene Templates hinzu
            for template in self.template_files:
                template_path = os.path.join(template_dir, template)
                if os.path.exists(template_path):
                    used_files.add(template_path)
            
            # Füge Template-Abhängigkeiten hinzu
            for dep in template_deps:
                dep_path = os.path.join(template_dir, dep)
                if os.path.exists(dep_path):
                    used_files.add(dep_path)
        
        # Füge statische Dateien hinzu
        static_dir = os.path.join(self.workspace_root, 'app', 'static')
        if os.path.exists(static_dir):
            for static_file in self.static_files:
                static_path = os.path.join(static_dir, static_file)
                if os.path.exists(static_path):
                    used_files.add(static_path)
        
        return used_files

    def find_all_project_files(self) -> Set[str]:
        """Findet alle Dateien im Projekt mit verbesserter Filterung"""
        project_files = set()
        
        for path in Path(self.workspace_root).rglob('*'):
            if path.is_file():
                # Prüfe auf ignorierte Muster
                if any(ignore in str(path) for ignore in self.ignored_patterns):
                    continue
                    
                # Prüfe Dateierweiterungen
                if path.suffix in self.ignored_extensions:
                    continue
                
                # Füge absolute Pfade hinzu
                project_files.add(str(path.absolute()))
        
        return project_files

    def analyze_files(self) -> Dict:
        """Hauptanalyse-Funktion"""
        logging.info("Starte Dateianalyse...")
        
        all_files = self.find_all_project_files()
        logging.info(f"Gefundene Projektdateien: {len(all_files)}")
        
        used_files = self.find_used_files()
        logging.info(f"Genutzte Dateien: {len(used_files)}")
        
        unused_files = all_files - used_files
        
        # Kategorisiere ungenutzte Dateien
        unused_by_type: Dict[str, List[str]] = {
            'python': [],
            'templates': [],
            'static': [],
            'other': []
        }
        
        for file in unused_files:
            if file.endswith('.py'):
                unused_by_type['python'].append(file)
            elif file.endswith('.html'):
                unused_by_type['templates'].append(file)
            elif '/static/' in file:
                unused_by_type['static'].append(file)
            else:
                unused_by_type['other'].append(file)
        
        # Erstelle detaillierten Report
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(all_files),
            'used_files': len(used_files),
            'unused_files': len(unused_files),
            'routes_found': list(self.known_routes),
            'unused_by_type': unused_by_type,
            'unused_files_list': sorted(list(unused_files))
        }
        
        # Speichere Report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"unused_files_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Erstelle Backup von potenziell ungenutzten Dateien
        for file in unused_files:
            self.create_backup(file)
        
        return report

def main():
    analyzer = FileAnalyzer()
    report = analyzer.analyze_files()
    
    print("\n=== Analyse-Ergebnisse ===")
    print(f"Gesamtanzahl Dateien: {report['total_files']}")
    print(f"Genutzte Dateien: {report['used_files']}")
    print(f"Ungenutzte Dateien: {report['unused_files']}")
    print("\nUngenutzte Dateien nach Typ:")
    for file_type, files in report['unused_by_type'].items():
        print(f"\n{file_type.upper()}: {len(files)} Dateien")
        for file in files[:5]:  # Zeige die ersten 5 Dateien jedes Typs
            print(f"- {os.path.relpath(file, analyzer.workspace_root)}")
        if len(files) > 5:
            print(f"... und {len(files) - 5} weitere")
    
    print(f"\nGefundene Routen: {len(report['routes_found'])}")
    print(f"\nDetaillierter Bericht wurde gespeichert in: {report['timestamp']}.json")
    print("\nBackups wurden erstellt im 'backups' Verzeichnis.")
    print("\nBitte prüfen Sie die Liste der ungenutzten Dateien sorgfältig,")
    print("bevor Sie Dateien endgültig löschen!")

if __name__ == '__main__':
    main() 