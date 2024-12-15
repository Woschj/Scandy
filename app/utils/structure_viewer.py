import os
import sqlite3
from pathlib import Path
from datetime import datetime

def print_database_structure():
    print("\nDatenbank-Struktur:")
    print("===================\n")
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'inventory.db')
    print(f"📁 Datenbank: {db_path}")
    
    # Dateiinformationen anzeigen
    if os.path.exists(db_path):
        size = os.path.getsize(db_path) / (1024 * 1024)  # Größe in MB
        modified = datetime.fromtimestamp(os.path.getmtime(db_path))
        print(f"   └─ Größe: {size:.2f} MB")
        print(f"   └─ Letzte Änderung: {modified}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Datenbankstatistiken
        cursor.execute("SELECT COUNT(*) FROM tools WHERE deleted = 0")
        tools_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM workers WHERE deleted = 0")
        workers_count = cursor.fetchone()[0]
        
        print(f"📊 Statistiken:")
        print(f"   └─ Aktive Werkzeuge: {tools_count}")
        print(f"   └─ Aktive Mitarbeiter: {workers_count}\n")
        
        # Tabellen und ihre Struktur
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"  📋 Tabelle: {table_name}")
            
            # Spalteninformationen
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for column in columns:
                nullable = "NULL" if column[3] == 0 else "NOT NULL"
                pk = "PRIMARY KEY" if column[5] == 1 else ""
                print(f"    └─ {column[1]} ({column[2]}) {nullable} {pk}".strip())
            
            # Anzahl der Einträge
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    └─ Einträge: {count}\n")
            
    except Exception as e:
        print(f"Fehler beim Lesen der Datenbankstruktur: {str(e)}")
    finally:
        conn.close()

def print_app_structure():
    print("\nApp-Struktur:")
    print("============\n")
    
    app_path = os.path.dirname(os.path.dirname(__file__))
    excluded_dirs = {'.git', '__pycache__', 'venv', 'env', 'node_modules'}
    excluded_files = {'*.pyc', '*.pyo', '*.pyd', '.DS_Store'}
    
    def should_include(path):
        return not any(excluded in path for excluded in excluded_dirs)
    
    for root, dirs, files in os.walk(app_path):
        if not should_include(root):
            continue
            
        level = root.replace(app_path, '').count(os.sep)
        indent = '  ' * level
        
        folder_name = os.path.basename(root)
        if level == 0:
            print(f"📁 app/")
        else:
            print(f"{indent}📁 {folder_name}/")
        
        subindent = '  ' * (level + 1)
        for file in sorted(files):
            if file.endswith(('.py', '.html', '.css', '.js')):
                print(f"{subindent}📄 {file}")

if __name__ == "__main__":
    print_database_structure()
    print_app_structure() 