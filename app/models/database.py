from flask import g, current_app
import sqlite3
from datetime import datetime
import os
import logging
from app.config import Config
import json
from pathlib import Path
import shutil

# Optional requests importieren
try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)

class Database:
    @classmethod
    def ensure_db_exists(cls):
        """Stellt sicher, dass die Datenbank existiert und initialisiert ist"""
        db_path = Config.get_absolute_database_path()
        
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        logger.info(f"=== CHECKING DATABASE AT STARTUP ===")
        logger.info(f"Configured database path: {Config.DATABASE_PATH}")
        logger.info(f"Absolute database path: {db_path}")
        
        # Wenn die Datenbank nicht existiert, erstelle sie
        if not os.path.exists(db_path):
            logger.info("Database does not exist, creating new one...")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cls._init_schema(conn)
            conn.close()
            logger.info("Database successfully initialized!")
        else:
            logger.info("Database already exists")
            # Aktualisiere Schema wenn nötig
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cls._init_schema(conn)
            conn.close()

    @staticmethod
    def get_db():
        """Gibt eine Datenbankverbindung zurück"""
        if hasattr(g, 'db'):
            logger.debug("Reusing existing database connection")
            return g.db
        
        db_path = os.path.join('app', 'database', 'inventory.db')
        logger.debug(f"Creating new database connection to {db_path}")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        
        return g.db

    @staticmethod
    def get_db_connection():
        """Direkter Datenbankzugriff für Verwaltungsaufgaben"""
        db_path = os.path.join('app', 'database', 'inventory.db')
        logger.debug(f"Creating direct database connection to {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def _init_schema(cls, conn):
        """Initialisiert das Datenbankschema"""
        logger.info("=== INITIALIZING DATABASE SCHEMA ===")
        
        # Hole existierende Tabellen
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        logger.info(f"Existing tables: {[t['name'] for t in tables]}")
        
        # Werkzeuge
        logger.info("Creating/updating tools table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT,
                category TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                sync_status TEXT DEFAULT 'pending'
            )
        ''')

        # Mitarbeiter
        logger.info("Creating/updating workers table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL UNIQUE,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                department TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                sync_status TEXT DEFAULT 'pending'
            )
        ''')

        # Verbrauchsmaterial
        logger.info("Creating/updating consumables table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS consumables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 0,
                category TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                sync_status TEXT DEFAULT 'pending'
            )
        ''')

        # Ausleihen
        logger.info("Creating/updating lendings table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS lendings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_barcode TEXT NOT NULL,
                worker_barcode TEXT NOT NULL,
                lent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                returned_at TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sync_status TEXT DEFAULT 'pending',
                FOREIGN KEY (tool_barcode) REFERENCES tools(barcode),
                FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
            )
        ''')

        # Verbrauchsmaterial-Nutzung
        logger.info("Creating/updating consumable_usages table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS consumable_usages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consumable_barcode TEXT NOT NULL,
                worker_barcode TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sync_status TEXT DEFAULT 'pending',
                FOREIGN KEY (consumable_barcode) REFERENCES consumables(barcode),
                FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
            )
        ''')

        # Benutzer
        logger.info("Creating/updating users table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        # Sync-Status
        logger.info("Creating/updating sync_status table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_sync TIMESTAMP,
                last_attempt TIMESTAMP,
                status TEXT,
                error TEXT
            )
        ''')

        # Einstellungen
        logger.info("Creating/updating settings table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT
            )
        ''')

        conn.commit()
        logger.info("Database schema initialization complete!")

    @staticmethod
    def init_db():
        """Initialisiert die Datenbank (für Flask-Kontext)"""
        with Database.get_db() as conn:
            Database._init_schema(conn)

    @staticmethod
    def close_db():
        db = g.pop('db', None)
        if db is not None:
            logger.debug("Closing database connection")
            db.close()

    @staticmethod
    def query(sql, params=None, one=False):
        """Führt eine Datenbankabfrage aus"""
        logger.info("\n=== DATABASE QUERY ===")
        logger.info(f"SQL: {sql}")
        logger.info(f"Parameters: {params}")
        
        try:
            with Database.get_db() as conn:
                if params:
                    cursor = conn.execute(sql, params)
                else:
                    cursor = conn.execute(sql)
                
                if one:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
                    
                logger.info(f"Number of results: {len(result) if result else 0}")
                if result and len(result) > 0:
                    logger.info(f"Example record: {dict(result[0] if not one else result)}")
                else:
                    logger.info("No results found")
                    
                return result
                
        except Exception as e:
            logger.error(f"\nDatabase error:")
            logger.error(f"Type: {type(e)}")
            logger.error(f"Message: {str(e)}")
            import traceback
            logger.error("Traceback:")
            logger.error(traceback.format_exc())
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

    @staticmethod
    def sync_with_server():
        """Synchronisiere lokale DB mit Server"""
        # Wenn wir auf dem Server sind oder requests nicht verfügbar ist, keine Synchronisation
        if Config.IS_SERVER or requests is None:
            return {'success': False, 'message': 'Synchronisation nicht verfügbar auf dem Server'}
            
        if not Config.SERVER_URL:
            return {'success': False, 'message': 'Keine Server-URL konfiguriert'}
            
        try:
            # Hole lokale Änderungen seit letzter Synchronisation
            last_sync = Database.get_last_sync_time()
            local_changes = Database.get_changes_since(last_sync)
            
            # Sende Änderungen an Server
            response = requests.post(
                f"{Config.SERVER_URL}/api/sync",
                json=local_changes
            )
            
            if response.status_code == 200:
                # Hole Server-Änderungen
                server_changes = response.json()
                
                # Wende Server-Änderungen an
                Database.apply_changes(server_changes)
                
                # Aktualisiere Sync-Zeitstempel
                Database.update_sync_time()
                
                return {'success': True, 'message': 'Synchronisation erfolgreich'}
            else:
                return {'success': False, 'message': f'Server-Fehler: {response.text}'}
                
        except Exception as e:
            return {'success': False, 'message': f'Sync-Fehler: {str(e)}'}
    
    @staticmethod
    def get_changes_since(timestamp):
        """Hole alle lokalen Änderungen seit timestamp"""
        changes = {
            'tools': [],
            'consumables': [],
            'workers': [],
            'lendings': []
        }
        
        # Hole geänderte Werkzeuge
        tools = Database.query('''
            SELECT * FROM tools 
            WHERE modified_at > ?
        ''', [timestamp])
        changes['tools'] = [dict(t) for t in tools]
        
        # Hole geänderte Verbrauchsmaterialien
        consumables = Database.query('''
            SELECT * FROM consumables 
            WHERE modified_at > ?
        ''', [timestamp])
        changes['consumables'] = [dict(c) for c in consumables]
        
        # ... ähnlich für workers und lendings
        
        return changes
    
    @staticmethod
    def apply_changes(changes):
        """Wende Server-Änderungen auf lokale DB an"""
        with Database.get_db() as conn:
            # Werkzeuge aktualisieren
            for tool in changes.get('tools', []):
                conn.execute('''
                    INSERT OR REPLACE INTO tools 
                    (barcode, name, category, location, deleted, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', [
                    tool['barcode'],
                    tool['name'],
                    tool['category'],
                    tool['location'],
                    tool['deleted'],
                    tool['modified_at']
                ])
            
            # ... ähnlich für andere Tabellen
            
            conn.commit()

    @staticmethod
    def init_sync_table():
        """Erstellt die Sync-Tabelle"""
        with Database.get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY,
                    last_sync TIMESTAMP,
                    last_attempt TIMESTAMP,
                    status TEXT,
                    error TEXT
                )
            ''')
            
            # Füge modified_at zu allen relevanten Tabellen hinzu
            tables = ['tools', 'consumables', 'workers', 'lendings']
            for table in tables:
                try:
                    conn.execute(f'ALTER TABLE {table} ADD COLUMN modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                    conn.execute(f'ALTER TABLE {table} ADD COLUMN sync_status TEXT DEFAULT "pending"')
                except:
                    pass  # Spalte existiert bereits

    @staticmethod
    def handle_sync_conflict(local_item, server_item):
        """Behandelt Konflikte zwischen lokalen und Server-Änderungen"""
        # Server gewinnt bei unterschiedlichen Zeitstempeln
        if server_item['modified_at'] > local_item['modified_at']:
            return server_item
        
        # Bei gleichem Zeitstempel, behalte gelöschte Items
        if server_item['modified_at'] == local_item['modified_at']:
            if server_item.get('deleted', False) or local_item.get('deleted', False):
                return {'deleted': True, **server_item}
            
        # Ansonsten behalte Server-Version
        return server_item

    @staticmethod
    def add_update_triggers():
        """Fügt Trigger für modified_at Updates hinzu"""
        with Database.get_db() as conn:
            tables = ['tools', 'consumables', 'workers', 'lendings']
            
            for table in tables:
                conn.execute(f'''
                    CREATE TRIGGER IF NOT EXISTS update_{table}_modified
                    AFTER UPDATE ON {table}
                    BEGIN
                        UPDATE {table} 
                        SET modified_at = CURRENT_TIMESTAMP,
                            sync_status = 'pending'
                        WHERE id = NEW.id;
                    END;
                ''')
                
                conn.execute(f'''
                    CREATE TRIGGER IF NOT EXISTS insert_{table}_modified
                    AFTER INSERT ON {table}
                    BEGIN
                        UPDATE {table}
                        SET modified_at = CURRENT_TIMESTAMP,
                            sync_status = 'pending'
                        WHERE id = NEW.id;
                    END;
                ''')

    @staticmethod
    def init_db_schema():
        """Initialisiert oder aktualisiert das Datenbankschema"""
        db_path = Database.get_database_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Erstelle zuerst alle Basistabellen
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    category TEXT,
                    location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0,
                    deleted_at TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT NOT NULL UNIQUE,
                    firstname TEXT NOT NULL,
                    lastname TEXT NOT NULL,
                    department TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0,
                    deleted_at TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS consumables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    quantity INTEGER DEFAULT 0,
                    min_quantity INTEGER DEFAULT 0,
                    category TEXT,
                    location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0,
                    deleted_at TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS lendings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_barcode TEXT NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    lent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    returned_at TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (tool_barcode) REFERENCES tools(barcode),
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS consumable_usages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumable_barcode TEXT NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (consumable_barcode) REFERENCES consumables(barcode),
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    last_sync TIMESTAMP,
                    last_attempt TIMESTAMP,
                    status TEXT,
                    error TEXT
                )
            ''')

            # Erstelle settings Tabelle mit vollständiger Struktur
            conn.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT
                )
            ''')
            
            # Füge Standardeinstellungen hinzu
            default_settings = [
                ('server_mode', '0', 'Aktiviert den Server-Modus (1) oder Client-Modus (0)'),
                ('server_url', '', 'URL des Sync-Servers im Client-Modus'),
                ('auto_sync', '0', 'Aktiviert automatische Synchronisation (1) oder nicht (0)')
            ]
            
            for key, value, description in default_settings:
                conn.execute('''
                    INSERT OR REPLACE INTO settings (key, value, description)
                    VALUES (?, ?, ?)
                ''', [key, value, description])
            
            # Füge einen initialen sync_status Eintrag hinzu
            conn.execute('''
                INSERT OR IGNORE INTO sync_status (last_sync, status)
                VALUES (NULL, 'never')
            ''')
            
            conn.commit()
            
        except Exception as e:
            print(f"Fehler bei der Datenbankinitialisierung: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def restore_from_backup(backup_path):
        """Stellt die Datenbank aus einem Backup wieder her"""
        db_path = Path(__file__).parent.parent / 'scandy.db'
        
        # Sicherungskopie der aktuellen Datenbank erstellen
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup = db_path.parent / f'pre_restore_backup_{timestamp}.db'
        
        try:
            # Aktuelle Datenbank sichern
            shutil.copy2(db_path, current_backup)
            
            # Backup wiederherstellen
            shutil.copy2(backup_path, db_path)
            logging.info(f"Datenbank erfolgreich wiederhergestellt von: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Wiederherstellen des Backups: {str(e)}")
            # Versuche die Sicherungskopie wiederherzustellen
            if current_backup.exists():
                shutil.copy2(current_backup, db_path)
            raise e
        finally:
            # Aufräumen
            if current_backup.exists():
                current_backup.unlink()

    @staticmethod
    def transaction():
        """Gibt eine Datenbankverbindung für eine Transaktion zurück"""
        conn = Database.get_db()
        conn.execute('BEGIN')
        return conn

    @staticmethod
    def get_departments():
        """Holt alle verfügbaren Abteilungen"""
        try:
            # Hole nur aktive Abteilungen (die mindestens einen aktiven Mitarbeiter haben oder kürzlich hinzugefügt wurden)
            departments = Database.query('''
                SELECT DISTINCT
                    s.value as name,
                    COALESCE(w.worker_count, 0) as worker_count
                FROM settings s
                LEFT JOIN (
                    SELECT department, COUNT(*) as worker_count
                    FROM workers
                    WHERE deleted = 0
                    GROUP BY department
                ) w ON w.department = s.value
                WHERE s.key LIKE 'department_%'
                AND s.value IS NOT NULL
                AND s.value != ''
                ORDER BY s.value
            ''')
            
            # Log für Debugging
            logger.info("=== DEPARTMENTS QUERY RESULTS ===")
            logger.info(f"Number of departments found: {len(departments)}")
            for dept in departments:
                logger.info(f"Department: {dict(dept)}")
            
            return departments
        except Exception as e:
            logger.error(f"Fehler beim Laden der Abteilungen: {str(e)}")
            return []

    @staticmethod
    def add_department(name):
        """Fügt eine neue Abteilung hinzu"""
        try:
            logger.info(f"\n=== ADDING DEPARTMENT {name} ===")
            
            # Prüfe ob die Abteilung bereits existiert
            existing = Database.query(
                'SELECT COUNT(*) as count FROM settings WHERE key = ? OR value = ?',
                [f"department_{name}", name],
                one=True
            )['count']
            
            if existing > 0:
                logger.error(f"Abteilung {name} existiert bereits")
                return {
                    'success': False,
                    'message': 'Abteilung existiert bereits'
                }
            
            # Füge neue Abteilung hinzu
            Database.query(
                'INSERT INTO settings (key, value, description) VALUES (?, ?, ?)',
                [f"department_{name}", name, 'Abteilung']
            )
            
            # Überprüfe ob die Abteilung wirklich hinzugefügt wurde
            added = Database.query(
                'SELECT COUNT(*) as count FROM settings WHERE key = ?',
                [f"department_{name}"],
                one=True
            )['count']
            
            if added == 0:
                logger.error(f"Abteilung {name} konnte nicht hinzugefügt werden")
                return {
                    'success': False,
                    'message': 'Abteilung konnte nicht hinzugefügt werden'
                }
            
            logger.info(f"Abteilung {name} wurde erfolgreich hinzugefügt")
            return {
                'success': True,
                'message': 'Abteilung erfolgreich hinzugefügt'
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Abteilung: {str(e)}")
            return {
                'success': False,
                'message': f'Datenbankfehler: {str(e)}'
            }

    @staticmethod
    def delete_department(name):
        """Löscht eine Abteilung"""
        try:
            logger.info(f"\n=== DELETING DEPARTMENT {name} ===")
            
            # Prüfe ob die Abteilung noch Mitarbeiter hat
            worker_count = Database.query(
                'SELECT COUNT(*) as count FROM workers WHERE department = ? AND deleted = 0',
                [name],
                one=True
            )['count']
            
            logger.info(f"Aktive Mitarbeiter in der Abteilung: {worker_count}")
            
            if worker_count > 0:
                logger.error(f"Abteilung {name} hat noch {worker_count} aktive Mitarbeiter")
                return {
                    'success': False,
                    'message': f'Abteilung hat noch {worker_count} aktive Mitarbeiter'
                }
            
            # Lösche die Abteilung aus der settings Tabelle
            Database.query(
                'DELETE FROM settings WHERE key = ?',
                [f"department_{name}"]
            )
            
            # Überprüfe ob die Löschung erfolgreich war
            remaining = Database.query(
                'SELECT COUNT(*) as count FROM settings WHERE key = ?',
                [f"department_{name}"],
                one=True
            )['count']
            
            if remaining > 0:
                logger.error(f"Abteilung {name} konnte nicht gelöscht werden")
                return {
                    'success': False,
                    'message': 'Abteilung konnte nicht gelöscht werden'
                }
            
            logger.info(f"Abteilung {name} wurde erfolgreich gelöscht")
            return {
                'success': True,
                'message': 'Abteilung erfolgreich gelöscht'
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Abteilung: {str(e)}")
            return {
                'success': False,
                'message': f'Datenbankfehler: {str(e)}'
            }

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