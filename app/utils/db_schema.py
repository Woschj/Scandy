import json
import os
from app.models.database import Database

class SchemaManager:
    SCHEMA_FILE = 'db_schema.json'
    
    @staticmethod
    def get_table_info(conn, table_name):
        """Liest die Spalteninformationen einer Tabelle aus"""
        columns_info = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {
            'columns': {
                column_info[1]: {  # column_info[1] ist der Spaltenname
                    'type': column_info[2],
                    'nullable': not column_info[3],
                    'primary_key': bool(column_info[5])
                } for column_info in columns_info
            }
        }

    @staticmethod
    def generate_schema():
        """Generiert das komplette Datenbankschema"""
        try:
            # Stelle sicher, dass das config-Verzeichnis existiert
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            with Database.get_db() as conn:
                # Alle Tabellen auslesen
                tables = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()
                
                schema = {}
                for table in tables:
                    table_name = table[0]
                    schema[table_name] = SchemaManager.get_table_info(conn, table_name)
                
                # Schema in JSON-Datei speichern
                schema_path = os.path.join(config_dir, SchemaManager.SCHEMA_FILE)
                with open(schema_path, 'w') as f:
                    json.dump(schema, f, indent=4)
                
                print(f"Datenbankschema wurde in {schema_path} gespeichert")
                return schema
                
        except Exception as e:
            print(f"Fehler beim Generieren des Schemas: {str(e)}")
            return {}  # Leeres Schema zurückgeben statt None

    @staticmethod
    def get_column_mapping():
        """Lädt die Spaltenzuordnungen aus der JSON-Datei"""
        try:
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            schema_path = os.path.join(config_dir, SchemaManager.SCHEMA_FILE)
            
            if not os.path.exists(schema_path):
                print("Schema-Datei nicht gefunden, generiere neu...")
                return SchemaManager.generate_schema()
                
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden des Schemas: {str(e)}")
            return SchemaManager.generate_schema()

    @staticmethod
    def build_select_query(table_name, columns=None, where=None):
        """Generiert dynamisch eine SELECT-Abfrage basierend auf dem Schema"""
        schema = SchemaManager.get_column_mapping()
        if not schema or table_name not in schema:
            print(f"Warnung: Keine Schema-Information für Tabelle {table_name}, verwende Standard-Query")
            # Fallback auf Standard-Query
            cols = '*' if not columns else ', '.join(columns)
            query = f"SELECT {cols} FROM {table_name}"
            if where:
                query += f" WHERE {where}"
            return query
            
        available_columns = schema[table_name]['columns'].keys()
        select_columns = columns if columns else available_columns
        
        query = f"SELECT {', '.join(select_columns)} FROM {table_name}"
        if where:
            query += f" WHERE {where}"
            
        return query

    @staticmethod
    def debug_schema():
        """Gibt das aktuelle Schema für Debug-Zwecke aus"""
        schema = SchemaManager.get_column_mapping()
        print("\n=== Aktuelles Datenbankschema ===")
        for table, info in schema.items():
            print(f"\nTabelle: {table}")
            for column, details in info['columns'].items():
                print(f"  - {column}: {details}")
        print("===============================\n")

    @staticmethod
    def update_schema(conn):
        """Führt notwendige Schema-Updates durch"""
        try:
            # Prüfen ob location/category Spalten existieren
            for table in ['consumables', 'tools']:
                columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
                column_names = [col[1] for col in columns]
                
                if 'location' not in column_names:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN location TEXT")
                if 'category' not in column_names:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN category TEXT")
            
            conn.commit()
            print(f"Schema erfolgreich aktualisiert")
            
        except Exception as e:
            print(f"Fehler beim Schema-Update: {str(e)}")
            raise

    @staticmethod
    def create_tables(conn):
        """Erstellt alle benötigten Tabellen"""
        conn.executescript('''
            -- ... bestehende Tabellen ...

            -- Consumables History Tabelle
            CREATE TABLE IF NOT EXISTS consumables_history (
                id INTEGER PRIMARY KEY,
                consumable_barcode TEXT NOT NULL,
                worker_barcode TEXT,
                quantity_change INTEGER NOT NULL,
                quantity_after INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                note TEXT,
                FOREIGN KEY (consumable_barcode) REFERENCES consumables(barcode),
                FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
            );
        ''')

    @staticmethod
    def init_settings():
        """Initialisiert die Grundeinstellungen in der Datenbank"""
        settings = [
            ('color_primary', '259 94% 51%'),
            ('color_primary_content', '0 0% 100%'),
            ('color_secondary', '314 100% 47%'),
            ('color_secondary_content', '0 0% 100%'),
            ('color_accent', '174 60% 51%'),
            ('color_accent_content', '0 0% 100%'),
            ('color_neutral', '219 14% 28%'),
            ('color_neutral_content', '0 0% 100%'),
            ('color_base', '0 0% 100%'),
            ('color_base_content', '219 14% 28%')
        ]
        
        with Database.get_db() as db:
            cursor = db.cursor()
            cursor.executemany(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                settings
            )
            db.commit()