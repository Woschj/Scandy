from flask import current_app
import os
from datetime import datetime
from ..models.database import Database

def print_database_structure():
    """Gibt die Struktur der Datenbank aus"""
    try:
        db_path = Database.DATABASE_PATH
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # Convert to MB
        last_modified = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        print("\nDatenbank-Struktur:")
        print("===================\n")
        print(f"📁 Datenbank: {db_path}")
        print(f"   └─ Größe: {db_size:.2f} MB")
        print(f"   └─ Letzte Änderung: {last_modified}")
        
        # Statistiken
        with Database.get_db() as db:
            cursor = db.cursor()
            
            # Aktive Einträge zählen
            tools = cursor.execute("SELECT COUNT(*) FROM tools WHERE deleted = 0").fetchone()[0]
            workers = cursor.execute("SELECT COUNT(*) FROM workers WHERE deleted = 0").fetchone()[0]
            
            print("\n📊 Statistiken:")
            print(f"   └─ Aktive Werkzeuge: {tools}")
            print(f"   └─ Aktive Mitarbeiter: {workers}\n")
            
            # Tabellenstruktur ausgeben
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                print(f"  📋 Tabelle: {table_name}")
                
                # Spalteninformationen
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    nullable = "NULL" if col[3] == 0 else "NOT NULL"
                    primary = "PRIMARY KEY" if col[5] == 1 else ""
                    print(f"└─ {col[1]} ({col[2]}) {nullable} {primary}".strip())
                
                # Anzahl der Einträge
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"    └─ Einträge: {count}\n")
                
    except Exception as e:
        print(f"Fehler beim Ausgeben der Datenbankstruktur: {e}")

def print_app_structure():
    """Gibt die Struktur der Flask-App aus"""
    app = current_app._get_current_object()
    
    print("\nApp-Struktur:")
    print("============\n")
    
    print("🔷 Registrierte Blueprints:")
    for blueprint in app.blueprints.values():
        print(f"   └─ {blueprint.name} (Prefix: {blueprint.url_prefix})")
    
    print("\n🔷 Verfügbare Routen:")
    for rule in app.url_map.iter_rules():
        print(f"   └─ {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    
    print("\n🔷 Template Ordner:")
    print(f"   └─ {app.template_folder}")
    
    print("\n🔷 Static Ordner:")
    print(f"   └─ {app.static_folder}") 