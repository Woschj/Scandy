class SchemaManager:
    def __init__(self, db):
        self.db = db

    def init_schema(self):
        """Initialisiert das Datenbankschema"""
        try:
            conn = self.db.get_db_connection()
            cursor = conn.cursor()
            
            # Admin-Tabelle hinzufügen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            
            # Admin-Account erstellen falls nicht vorhanden
            cursor.execute("""
                INSERT OR IGNORE INTO admin (username, password)
                VALUES ('admin', 'admin')
            """)
            
            conn.commit()
            
        except Exception as e:
            print(f"Fehler beim Initialisieren des Schemas: {e}")
            conn.rollback()
        finally:
            conn.close()
        
    def init_settings(self):
        """Initialisiert die Grundeinstellungen in der Datenbank"""
        default_settings = {
            'theme': 'light',
            'language': 'de',
            'items_per_page': '10'
            # Fügen Sie hier weitere Standardeinstellungen hinzu
        }
        
        try:
            conn = self.db.get_db_connection()
            cursor = conn.cursor()
            
            for key, value in default_settings.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO settings (key, value)
                    VALUES (?, ?)
                """, (key, value))
            conn.commit()
            
        except Exception as e:
            print(f"Fehler beim Initialisieren der Einstellungen: {e}")
            conn.rollback()
        finally:
            conn.close()
        
    def reset_schema(self):
        """Löscht und erstellt das Schema neu"""
        try:
            conn = self.db.get_db_connection()
            cursor = conn.cursor()
            
            # Vorsicht: Dies löscht alle Daten!
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            
            conn.commit()
            self.init_schema()
            
        except Exception as e:
            print(f"Fehler beim Zurücksetzen des Schemas: {e}")
            conn.rollback()
        finally:
            conn.close()
        
    def init_tables(self):
        """Initialisiert alle Tabellen"""
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ...
            )
        ''')
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS consumable_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consumable_id INTEGER NOT NULL,
                worker_barcode TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (consumable_id) REFERENCES consumables(id),
                FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
            )
        ''')