import sqlite3
import os

def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'inventory.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_database():
    try:
        with get_db_connection() as conn:
            print("Starting database migration...")

            # Füge return_time zu consumable_lendings hinzu
            try:
                conn.execute('''
                    ALTER TABLE consumable_lendings 
                    ADD COLUMN return_time TIMESTAMP
                ''')
                print("Added return_time to consumable_lendings")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("return_time column already exists")
                else:
                    raise e

            # Bestehende Migrationen...
            try:
                conn.execute('''
                    ALTER TABLE consumables_history 
                    ADD COLUMN old_quantity INTEGER
                ''')
                conn.execute('''
                    ALTER TABLE consumables_history 
                    ADD COLUMN new_quantity INTEGER
                ''')
                print("Added quantity columns to consumables_history")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("quantity columns already exist")
                else:
                    raise e

            # Erstelle consumable_lendings Tabelle
            conn.execute('''
                CREATE TABLE IF NOT EXISTS consumable_lendings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumable_barcode TEXT NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    lending_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consumable_barcode) REFERENCES consumables(barcode),
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                )
            ''')

            # Erweitere consumables
            conn.execute('''
                ALTER TABLE consumables 
                ADD COLUMN max_bestand INTEGER;
            ''')
            conn.execute('''
                ALTER TABLE consumables 
                ADD COLUMN lieferant TEXT;
            ''')
            conn.execute('''
                ALTER TABLE consumables 
                ADD COLUMN bestellnummer TEXT;
            ''')

            # Erweitere system_logs
            conn.execute('''
                ALTER TABLE system_logs 
                ADD COLUMN related_barcode TEXT;
            ''')
            conn.execute('''
                ALTER TABLE system_logs 
                ADD COLUMN details TEXT;
            ''')

            conn.commit()
            print("Database migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise e

def add_system_logs_table():
    try:
        with get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    user_id INTEGER,
                    action TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            print("System-Logs Tabelle erfolgreich erstellt!")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("System-Logs Tabelle existiert bereits.")
        else:
            print(f"Fehler beim Erstellen der System-Logs Tabelle: {str(e)}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {str(e)}")

def add_image_columns():
    try:
        with get_db_connection() as conn:
            # Liste der Tabellen, die eine image-Spalte bekommen sollen
            tables = ['tools', 'consumables', 'categories']
            
            for table in tables:
                try:
                    conn.execute(f'''
                        ALTER TABLE {table}
                        ADD COLUMN image BLOB;
                    ''')
                    print(f"Image-Spalte zur Tabelle '{table}' hinzugefügt!")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"Image-Spalte existiert bereits in Tabelle '{table}'")
                    else:
                        print(f"Fehler beim Hinzufügen der Image-Spalte zu '{table}': {str(e)}")
            
            conn.commit()
            print("Migration erfolgreich abgeschlossen!")
    except Exception as e:
        print(f"Unerwarteter Fehler: {str(e)}")

if __name__ == "__main__":
    print("Starting migration script...")
    migrate_database()
    print("Migration script completed!")