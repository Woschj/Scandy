import os
import sys
from pathlib import Path
import importlib.util
import inspect
import flask
from app import create_app
from app.models.database import Database

class AppUsageAnalyzer:
    def __init__(self):
        self.app = create_app()
        self.used_files = set()
        self.used_templates = set()
        self.used_static_files = set()
        self.all_routes = []
        self.workspace_root = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # Ordner die ignoriert werden sollen
        self.excluded_dirs = {
            'venv',
            '.venv',
            'env',
            '.env',
            '__pycache__',
            '.git',
            '.idea',
            '.vscode',
            'node_modules',
            'dist',
            'build',
            'migrations'
        }

    def should_skip_path(self, path):
        """Prüft, ob ein Pfad übersprungen werden soll"""
        path_parts = Path(path).parts
        return any(excluded in path_parts for excluded in self.excluded_dirs)

    def analyze_routes(self):
        """Analysiert alle registrierten Routen der App"""
        print("\n=== Analysiere Routen ===")
        with self.app.test_request_context():
            for rule in self.app.url_map.iter_rules():
                # Ignoriere statische Routen
                if rule.endpoint != 'static':
                    self.all_routes.append({
                        'endpoint': rule.endpoint,
                        'methods': list(rule.methods),
                        'path': rule.rule
                    })
                    print(f"Route gefunden: {rule.endpoint} ({rule.rule})")

                    # Finde die View-Funktion
                    view_function = self.app.view_functions[rule.endpoint]
                    if view_function:
                        module = inspect.getmodule(view_function)
                        if module and not self.should_skip_path(module.__file__):
                            self.used_files.add(module.__file__)
                            print(f"  - Modul: {module.__file__}")

    def analyze_templates(self):
        """Analysiert alle verwendeten Templates"""
        print("\n=== Analysiere Templates ===")
        template_dir = self.workspace_root / 'app' / 'templates'
        if template_dir.exists():
            for template in template_dir.rglob('*.html'):
                if self.should_skip_path(template):
                    continue
                try:
                    with open(template, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Suche nach extends und include Statements
                        if '{% extends' in content or '{% include' in content:
                            self.used_templates.add(template)
                            print(f"Template mit Abhängigkeiten gefunden: {template}")
                except Exception as e:
                    print(f"Fehler beim Lesen von {template}: {e}")

    def analyze_static_files(self):
        """Analysiert alle statischen Dateien"""
        print("\n=== Analysiere Statische Dateien ===")
        static_dir = self.workspace_root / 'app' / 'static'
        if static_dir.exists():
            for static_file in static_dir.rglob('*.*'):
                if self.should_skip_path(static_file):
                    continue
                if static_file.suffix in ['.js', '.css', '.png', '.jpg', '.svg']:
                    self.used_static_files.add(static_file)
                    print(f"Statische Datei gefunden: {static_file}")

    def analyze_python_imports(self):
        """Analysiert Python-Imports in allen .py Dateien"""
        print("\n=== Analysiere Python-Imports ===")
        for py_file in self.workspace_root.rglob('*.py'):
            if self.should_skip_path(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Suche nach Import-Statements
                    if 'import' in content or 'from' in content:
                        self.used_files.add(py_file)
                        print(f"Python-Datei mit Imports gefunden: {py_file}")
            except Exception as e:
                print(f"Fehler beim Lesen von {py_file}: {e}")

    def find_unused_files(self):
        """Findet nicht verwendete Dateien"""
        print("\n=== Nicht verwendete Dateien ===")
        all_files = set()
        
        # Sammle alle Dateien
        for ext in ['.py', '.html', '.js', '.css']:
            for file in self.workspace_root.rglob(f'*{ext}'):
                if not self.should_skip_path(file):
                    all_files.add(file)

        # Finde nicht verwendete Dateien
        unused_files = all_files - self.used_files - self.used_templates - self.used_static_files
        
        if unused_files:
            print("\nFolgende Dateien scheinen nicht verwendet zu werden:")
            for file in sorted(unused_files):
                print(f"- {file}")
        else:
            print("Keine ungenutzten Dateien gefunden.")

    def run_analysis(self):
        """Führt die komplette Analyse durch"""
        print("Starte Analyse der App-Nutzung...")
        print(f"Workspace Root: {self.workspace_root}")
        print(f"Ignorierte Ordner: {', '.join(self.excluded_dirs)}")
        
        self.analyze_routes()
        self.analyze_templates()
        self.analyze_static_files()
        self.analyze_python_imports()
        self.find_unused_files()

        print("\n=== Analyse abgeschlossen ===")
        print(f"Gefundene Routen: {len(self.all_routes)}")
        print(f"Verwendete Python-Dateien: {len(self.used_files)}")
        print(f"Verwendete Templates: {len(self.used_templates)}")
        print(f"Verwendete Statische Dateien: {len(self.used_static_files)}")

def main():
    analyzer = AppUsageAnalyzer()
    analyzer.run_analysis()

if __name__ == '__main__':
    main() 