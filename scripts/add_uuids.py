import sqlite3
from pathlib import Path

def init_db():
    """Führt die UUID-Migration durch"""
    print("Starte UUID-Migration...")
    
    # Pfad zur Datenbank
    db_path = Path(__file__).parent.parent / 'instance' / 'scandy.db'
    
    if not db_path.exists():
        print(f"Fehler: Datenbank nicht gefunden unter {db_path}")
        return
    
    try:
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # SQL-Datei lesen
        migration_path = Path(__file__).parent.parent / 'migrations' / 'add_uuid_columns.sql'
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        # Migration ausführen
        print("Führe Datenbankänderungen durch...")
        
        # SQL-Befehle aufteilen und einzeln ausführen
        for command in migration_sql.split(';'):
            if command.strip():
                cur.execute(command)
                
        # Änderungen speichern
        conn.commit()
        
        # Prüfen ob UUIDs generiert wurden
        tables = ['tools', 'consumables', 'workers']
        for table in tables:
            cur.execute(f"SELECT COUNT(*) as total, COUNT(uuid) as with_uuid FROM {table}")
            total, with_uuid = cur.fetchone()
            print(f"{table}: {with_uuid}/{total} UUIDs generiert")
        
        print("\nMigration erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"Fehler bei der Migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    init_db() 