import sqlite3
import os

def list_app_files():
    """Listet alle für die App relevanten Dateien auf"""
    app_files = []
    
    # Durchsuche das app-Verzeichnis rekursiv
    for root, dirs, files in os.walk('app'):
        # Ignoriere __pycache__ Verzeichnisse
        if '__pycache__' in root:
            continue
            
        for file in files:
            # Nur Python, SQL, HTML und JavaScript Dateien
            if file.endswith(('.py', '.sql', '.html', '.js')):
                full_path = os.path.join(root, file)
                app_files.append(full_path)
    
    print("\n=== APP DATEIEN ===")
    for file in sorted(app_files):
        print(f"📄 {file}")
    print("=================\n")

def run_migration():
    # Debug: Liste alle App-Dateien
    list_app_files()
    
    # Verbindung zur Datenbank herstellen
    db_path = os.path.join('app', 'database', 'inventory.db')
    print(f"Versuche Verbindung zur Datenbank: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"FEHLER: Datenbank existiert nicht unter: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    
    try:
        # Migration-Datei lesen
        migration_path = 'app/migrations/008_add_tool_status_changes.sql'
        print(f"Lese Migration aus: {os.path.abspath(migration_path)}")
        
        if not os.path.exists(migration_path):
            print(f"FEHLER: Migrationsdatei existiert nicht unter: {migration_path}")
            return
            
        with open(migration_path, 'r') as f:
            sql = f.read()
            print(f"SQL zum Ausführen:\n{sql}")
            
        # SQL ausführen
        conn.executescript(sql)
        conn.commit()
        
        # Prüfen ob Tabelle erstellt wurde
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tool_status_changes'")
        if cursor.fetchone():
            print("Migration erfolgreich - Tabelle wurde erstellt!")
        else:
            print("FEHLER: Tabelle wurde nicht erstellt!")
        
    except Exception as e:
        print(f"Fehler bei der Migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration() 