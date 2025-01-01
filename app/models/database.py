from flask import g, current_app
import sqlite3
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class Database:
    DATABASE_PATH = os.path.join('database', 'inventory.db')

    @classmethod
    def ensure_db_exists(cls):
        """Stellt sicher, dass die Datenbank existiert und initialisiert ist"""
        db_path = cls.get_database_path()
        
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        print(f"Überprüfe Datenbank in: {db_path}")
        
        # Wenn die Datenbank nicht existiert, erstelle sie
        if not os.path.exists(db_path):
            print("Erstelle neue Datenbank...")
            conn = sqlite3.connect(db_path)
            conn.close()
            # Initialisiere die Datenbankstruktur
            cls.init_db()
            print("Datenbank erfolgreich initialisiert!")
        else:
            print("Datenbank existiert bereits")

        # Überprüfe ob alle Tabellen existieren
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        if not tables:
            print("Keine Tabellen gefunden, initialisiere Datenbankstruktur...")
            conn.close()
            cls.init_db()
        else:
            print(f"Gefundene Tabellen: {[table[0] for table in tables]}")
            conn.close()

    @staticmethod
    def get_database_path():
        """Gibt den Pfad zur Datenbank zurück"""
        # Basis-Pfad ist das app-Verzeichnis
        base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_path, 'database', 'inventory.db')
    
    @staticmethod
    def get_db():
        if 'db' not in g:
            db_path = Database.get_database_path()
            
            # Stelle sicher, dass die Datenbank existiert
            Database.ensure_db_exists()
            
            # Verbindung herstellen
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            
        return g.db

    @staticmethod
    def get_db_connection():
        """Direkter Datenbankzugriff für Verwaltungsaufgaben"""
        db_path = Database.get_database_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        """Initialisiert die Datenbankstruktur"""
        conn = Database.get_db_connection()
        cursor = conn.cursor()
        
        # Settings-Tabelle erstellen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Standard-Einstellungen einfügen
        default_settings = [
            ('primary_color', '220 35% 45%'),  # BTZ-Blau
            ('secondary_color', '220 35% 35%'),  # Dunkleres BTZ-Blau
            ('accent_color', '220 35% 55%'),  # Helleres BTZ-Blau
            ('theme', 'light'),
            ('items_per_page', '10')
        ]
        
        for key, value in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
        
        # Indizes für bessere Performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_deleted ON tools(deleted)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_barcode ON tools(barcode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workers_deleted ON workers(deleted)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workers_barcode ON workers(barcode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumables_deleted ON consumables(deleted)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lendings_tool ON lendings(tool_barcode)')
        
        conn.commit()

    @staticmethod
    def close_db():
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @staticmethod
    def query(query, args=None, one=False):
        print(f"\n=== Database Query ===")
        print(f"Query: {query}")
        print(f"Args: {args}")
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                result = cursor.execute(query, args or [])
                if one:
                    print("Hole einen Datensatz...")
                    return result.fetchone()
                print("Hole alle Datensätze...")
                return result.fetchall()
        except Exception as e:
            print(f"FEHLER bei Datenbankabfrage: {str(e)}")
            raise

    def create_lending(self, tool_barcode, worker_barcode):
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Prüfen ob das Tool bereits ausgeliehen ist
                cursor.execute("""
                    SELECT id FROM lendings 
                    WHERE tool_barcode = ? 
                    AND returned_at IS NULL
                """, (tool_barcode,))
                
                if cursor.fetchone():
                    return {
                        'success': False,
                        'message': 'Werkzeug ist bereits ausgeliehen'
                    }
                
                # Neue Ausleihe eintragen
                cursor.execute("""
                    INSERT INTO lendings (
                        tool_barcode, 
                        worker_barcode, 
                        lent_at
                    ) VALUES (?, ?, datetime('now'))
                """, (tool_barcode, worker_barcode))
                
                lending_id = cursor.lastrowid
                conn.commit()
                
                return {
                    'success': True,
                    'lending_id': lending_id,
                    'message': 'Ausleihe erfolgreich eingetragen'
                }
                
        except Exception as e:
            logger.error(f"Error creating lending: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Datenbankfehler: {str(e)}'
            }

    def update_tool_status(self, barcode, status):
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tools 
                    SET status = ? 
                    WHERE barcode = ?
                """, (status, barcode))
                
                if cursor.rowcount == 0:
                    return {
                        'success': False,
                        'message': 'Werkzeug nicht gefunden'
                    }
                    
                conn.commit()
                return {
                    'success': True,
                    'message': 'Status erfolgreich aktualisiert'
                }
                
        except Exception as e:
            logger.error(f"Error updating tool status: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Datenbankfehler: {str(e)}'
            }

    def get_tool_by_barcode(self, barcode):
        """Werkzeug anhand des Barcodes abrufen"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, barcode, name, description, status, 
                           created_at, deleted, location, category
                    FROM tools 
                    WHERE barcode = ? AND deleted = 0
                """, (barcode,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'barcode': row[1],
                        'name': row[2],
                        'description': row[3],
                        'status': row[4],
                        'created_at': row[5],
                        'deleted': row[6],
                        'location': row[7],
                        'category': row[8]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting tool: {str(e)}", exc_info=True)
            return None

    def get_worker_by_barcode(self, barcode):
        """Mitarbeiter anhand des Barcodes abrufen"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, barcode, firstname, lastname, 
                           department, email, created_at, deleted
                    FROM workers 
                    WHERE barcode = ? AND deleted = 0
                """, (barcode,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'barcode': row[1],
                        'firstname': row[2],
                        'lastname': row[3],
                        'department': row[4],
                        'email': row[5],
                        'created_at': row[6],
                        'deleted': row[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting worker: {str(e)}", exc_info=True)
            return None

    def delete_lending(self, lending_id):
        """Ausleihe löschen (für Rollback)"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM lendings 
                    WHERE id = ?
                """, (lending_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting lending: {str(e)}", exc_info=True)
            return False

    def get_active_lending(self, tool_barcode):
        """Aktive Ausleihe für ein Werkzeug abrufen"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        l.id,
                        l.tool_barcode,
                        l.worker_barcode,
                        l.lent_at,
                        w.firstname || ' ' || w.lastname as worker_name
                    FROM lendings l
                    JOIN workers w ON l.worker_barcode = w.barcode
                    WHERE l.tool_barcode = ? 
                    AND l.returned_at IS NULL
                """, (tool_barcode,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'tool_barcode': row[1],
                        'worker_barcode': row[2],
                        'lent_at': row[3],
                        'worker_name': row[4]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting active lending: {str(e)}", exc_info=True)
            return None

    def return_tool(self, tool_barcode):
        """Werkzeug zurückgeben"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Aktive Ausleihe aktualisieren
                cursor.execute("""
                    UPDATE lendings 
                    SET returned_at = datetime('now')
                    WHERE tool_barcode = ? 
                    AND returned_at IS NULL
                """, (tool_barcode,))
                
                if cursor.rowcount == 0:
                    return {
                        'success': False,
                        'message': 'Keine aktive Ausleihe gefunden'
                    }
                    
                conn.commit()
                return {
                    'success': True,
                    'message': 'Rückgabe erfolgreich eingetragen'
                }
                
        except Exception as e:
            logger.error(f"Error returning tool: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Datenbankfehler: {str(e)}'
            }

    def soft_delete_tool(self, barcode):
        """Verschiebt ein Werkzeug in den Papierkorb"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Prüfen ob das Werkzeug ausgeliehen ist
                cursor.execute("""
                    SELECT COUNT(*) FROM lendings 
                    WHERE tool_barcode = ? AND returned_at IS NULL
                """, (barcode,))
                
                if cursor.fetchone()[0] > 0:
                    return {
                        'success': False,
                        'message': 'Werkzeug kann nicht gelöscht werden, da es noch ausgeliehen ist.'
                    }
                
                # Werkzeug als gelöscht markieren
                cursor.execute("""
                    UPDATE tools 
                    SET deleted = 1, 
                        deleted_at = datetime('now')
                    WHERE barcode = ?
                """, (barcode,))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': 'Werkzeug wurde in den Papierkorb verschoben'
                }
                
        except Exception as e:
            logger.error(f"Error deleting tool: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Datenbankfehler: {str(e)}'
            }

    @staticmethod
    def soft_delete(table, barcode):
        """Verschiebt einen Eintrag in den Papierkorb"""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                
                # Prüfe bei Werkzeugen ob sie ausgeliehen sind
                if table == 'tools':
                    cursor.execute("""
                        SELECT COUNT(*) FROM lendings 
                        WHERE tool_barcode = ? AND returned_at IS NULL
                    """, [barcode])
                    if cursor.fetchone()[0] > 0:
                        return {
                            'success': False,
                            'message': 'Werkzeug ist noch ausgeliehen'
                        }
                
                # Prüfe ob der Eintrag existiert
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE barcode = ? AND deleted = 0
                """, [barcode])
                if cursor.fetchone()[0] == 0:
                    return {
                        'success': False,
                        'message': 'Eintrag nicht gefunden'
                    }
                
                cursor.execute(f"""
                    UPDATE {table}
                    SET deleted = 1,
                        deleted_at = datetime('now')
                    WHERE barcode = ?
                """, [barcode])
                conn.commit()
                return {
                    'success': True,
                    'message': 'In Papierkorb verschoben'
                }
        except Exception as e:
            logger.error(f"Fehler beim Soft-Delete: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    @staticmethod
    def restore_item(table, barcode):
        """Stellt einen Eintrag aus dem Papierkorb wieder her"""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                
                # Prüfe ob der Eintrag im Papierkorb ist
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE barcode = ? AND deleted = 1
                """, [barcode])
                if cursor.fetchone()[0] == 0:
                    return {
                        'success': False,
                        'message': 'Eintrag nicht im Papierkorb gefunden'
                    }
                
                cursor.execute(f"""
                    UPDATE {table}
                    SET deleted = 0,
                        deleted_at = NULL
                    WHERE barcode = ?
                """, [barcode])
                conn.commit()
                return {
                    'success': True,
                    'message': 'Erfolgreich wiederhergestellt'
                }
        except Exception as e:
            logger.error(f"Fehler bei der Wiederherstellung: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    @staticmethod
    def permanent_delete(table, barcode):
        """Löscht einen Eintrag endgültig"""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                
                # Prüfe ob der Eintrag im Papierkorb ist
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE barcode = ? AND deleted = 1
                """, [barcode])
                if cursor.fetchone()[0] == 0:
                    return {
                        'success': False,
                        'message': 'Eintrag nicht im Papierkorb gefunden'
                    }
                
                cursor.execute(f"""
                    DELETE FROM {table}
                    WHERE barcode = ?
                """, [barcode])
                conn.commit()
                return {
                    'success': True,
                    'message': 'Endgültig gelöscht'
                }
        except Exception as e:
            logger.error(f"Fehler beim endgültigen Löschen: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def _run_migrations(self):
        migrations = [
            '001_initial_schema.sql',
            '002_add_deleted_column.sql',
            '003_add_timestamps.sql',
            '004_add_categories.sql',
            '005_add_description.sql',
            '006_add_stock_threshold.sql',
            '007_add_consumable_usage_table.sql',
        ]

def init_db():
    """Initialisiert die Datenbank"""
    # Erst Database.init_db() aufrufen um die Tabellen zu erstellen
    Database.init_db()
    
    # Dann die Spalten hinzufügen
    with Database.get_db() as conn:
        # Prüfe existierende Spalten in tools
        columns_tools = conn.execute('PRAGMA table_info(tools)').fetchall()
        existing_columns_tools = [column[1] for column in columns_tools]

        # Prüfe existierende Spalten in consumables
        columns_consumables = conn.execute('PRAGMA table_info(consumables)').fetchall()
        existing_columns_consumables = [column[1] for column in columns_consumables]

        # Füge fehlende Spalten zu tools hinzu
        if 'category' not in existing_columns_tools:
            conn.execute('ALTER TABLE tools ADD COLUMN category TEXT')
        if 'location' not in existing_columns_tools:
            conn.execute('ALTER TABLE tools ADD COLUMN location TEXT')

        # Füge fehlende Spalten zu consumables hinzu
        if 'category' not in existing_columns_consumables:
            conn.execute('ALTER TABLE consumables ADD COLUMN category TEXT')
        if 'location' not in existing_columns_consumables:
            conn.execute('ALTER TABLE consumables ADD COLUMN location TEXT')

        conn.commit()

class BaseModel:
    TABLE_NAME = None
    
    @classmethod
    def get_all_active(cls):
        return Database.query(f"SELECT * FROM {cls.TABLE_NAME} WHERE deleted = 0")

    @classmethod
    def get_by_id(cls, id):
        return Database.query(
            f"SELECT * FROM {cls.TABLE_NAME} WHERE id = ? AND deleted = 0", 
            [id], 
            one=True
        )

    @classmethod
    def get_by_barcode(cls, barcode):
        return Database.query(
            f"SELECT * FROM {cls.TABLE_NAME} WHERE barcode = ? AND deleted = 0", 
            [barcode], 
            one=True
        )

def init_database():
    """Initialisiert die Datenbank"""
    if not os.path.exists('database'):
        os.makedirs('database')

def close_db(e=None):
    """Schließt die Datenbankverbindung"""
    db = g.pop('db', None)
    
    if db is not None:
        db.close()

def show_db_structure():
    """Zeigt die Struktur der Datenbank an"""
    db = get_db_connection()
    cursor = db.cursor()
    
    # Tabellen auflisten
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    structure = []
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        table_info = {
            'name': table_name,
            'columns': [{'name': col[1], 'type': col[2]} for col in columns]
        }
        structure.append(table_info)
    
    db.close()
    return structure

def get_db_connection():
    return Database.get_db_connection()

__all__ = [
    'Database', 
    'BaseModel',
    'get_db_connection',
    'init_database',
    'close_db',
    'show_db_structure'
]

class Tool:
    @staticmethod
    def count_active():
        """Zählt alle aktiven (nicht gelöschten) Werkzeuge"""
        db = get_db('inventory.db')
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM tools WHERE deleted = 0 OR deleted IS NULL')
        return cursor.fetchone()[0]

class Consumable:
    @staticmethod
    def count_active():
        """Zählt alle aktiven (nicht gelöschten) Verbrauchsmaterialien"""
        db = get_db('inventory.db')
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM consumables WHERE deleted = 0 OR deleted IS NULL')
        return cursor.fetchone()[0]

class Worker:
    @staticmethod
    def count_active():
        """Zählt alle aktiven (nicht gelöschten) Mitarbeiter"""
        db = get_db('inventory.db')
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM workers WHERE deleted = 0 OR deleted IS NULL')
        return cursor.fetchone()[0]

def create_tables():
    init_db()