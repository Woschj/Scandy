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
    """Datenbankklasse für SQLite"""
    
    @classmethod
    def ensure_db_exists(cls):
        """Stellt sicher, dass die Datenbank existiert und initialisiert ist"""
        logging.info("=== CHECKING DATABASE AT STARTUP ===")
        
        # Verwende den korrekten Pfad aus der Config
        db_path = Config.DATABASE
        
        logging.info(f"Configured database path: {db_path}")
        logging.info(f"Absolute database path: {os.path.abspath(db_path)}")
        
        # Stelle sicher, dass das Verzeichnis existiert
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        db_exists = os.path.exists(db_path)
        logging.info(f"Database exists: {db_exists}")
        
        if db_exists:
            # Prüfe ob die Datenbank lesbar ist und Daten enthält
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Prüfe Tabellen
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                table_names = [t[0] for t in tables]
                logging.info(f"Found tables: {table_names}")
                
                # Prüfe Inhalte
                for table in table_names:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    logging.info(f"Table {table} contains {count} entries")
                
                conn.close()
                
                if not tables:
                    logging.warning("Database exists but contains no tables")
                    return False
                    
                return True
                
            except Exception as e:
                logging.error(f"Error reading database: {str(e)}")
                return False
        else:
            logging.info("Creating new database")
            try:
                conn = sqlite3.connect(db_path)
                conn.close()
                return True
            except Exception as e:
                logging.error(f"Error creating database: {str(e)}")
                return False
    
    @classmethod
    def get_db_connection(cls):
        """Gibt eine neue Datenbankverbindung zurück"""
        from app.config import config
        current_config = config['default']()
        conn = sqlite3.connect(current_config.DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    
    @classmethod
    def get_db(cls):
        """Gibt eine Datenbankverbindung aus dem Anwendungskontext zurück"""
        if 'db' not in g:
            g.db = sqlite3.connect(Config.DATABASE)
            g.db.row_factory = sqlite3.Row
            
            # Debug: Prüfe Tabelleninhalte beim ersten Verbindungsaufbau
            cursor = g.db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                logging.info(f"Tabelle {table_name} enthält {count} Einträge")
                
        return g.db
    
    @classmethod
    def show_db_structure(cls):
        """Zeigt die Struktur der Datenbank an"""
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        structure = {}
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            structure[table_name] = [column[1] for column in columns]
        
        conn.close()
        return structure
    
    @staticmethod
    def query(sql, params=None, one=False):
        """Führt eine Datenbankabfrage aus"""
        logging.info("\n=== DATABASE QUERY ===")
        logging.info(f"SQL: {sql}")
        logging.info(f"Parameters: {params}")
        
        try:
            conn = Database.get_db()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
                
            if one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            
            # Debug-Ausgaben
            if result:
                logging.info(f"Number of results: {len([result] if one else result)}")
                logging.info(f"Example record: {dict(result if one else result[0])}")
            else:
                logging.info("No results returned")
                
            return result
            
        except Exception as e:
            logging.error(f"Datenbankfehler: {str(e)}")
            logging.error(f"Query: {sql}")
            logging.error(f"Parameters: {params}")
            raise
    
    @classmethod
    def get_departments(cls):
        """Gibt alle Abteilungen mit der Anzahl der zugeordneten Mitarbeiter zurück"""
        try:
            departments = cls.query("""
                SELECT 
                    REPLACE(key, 'department_', '') as name,
                    value,
                    COUNT(workers.id) as worker_count
                FROM settings
                LEFT JOIN workers ON workers.department = settings.value AND workers.deleted = 0
                WHERE key LIKE 'department_%'
                GROUP BY settings.key, settings.value
                ORDER BY value
            """)
            
            return [{'name': dept['value'], 'worker_count': dept['worker_count']} for dept in departments]
        except Exception as e:
            logging.error(f"Fehler beim Laden der Abteilungen: {str(e)}")
            return []
    
    @classmethod
    def get_locations(cls, usage=None):
        """Gibt alle Standorte mit der Anzahl der zugeordneten Werkzeuge und Verbrauchsmaterialien zurück"""
        try:
            # Basis-Query
            query = """
                SELECT 
                    REPLACE(key, 'location_', '') as name,
                    value,
                    description as usage,
                    (SELECT COUNT(*) FROM tools WHERE location = settings.value AND deleted = 0) as tools_count,
                    (SELECT COUNT(*) FROM consumables WHERE location = settings.value AND deleted = 0) as consumables_count
                FROM settings
                WHERE key LIKE 'location_%'
            """
            
            # Füge Verwendungszweck-Filter hinzu
            if usage == 'tools':
                query += " AND (description = 'tools' OR description = 'both')"
            elif usage == 'consumables':
                query += " AND (description = 'consumables' OR description = 'both')"
            
            query += " ORDER BY value"
            
            locations = cls.query(query)
            return [
                {
                    'name': loc['value'],
                    'usage': loc['usage'],
                    'tools_count': loc['tools_count'],
                    'consumables_count': loc['consumables_count']
                }
                for loc in locations
            ]
        except Exception as e:
            logging.error(f"Fehler beim Laden der Standorte: {str(e)}")
            return []
    
    @classmethod
    def get_categories(cls, usage=None):
        """Gibt alle Kategorien mit der Anzahl der zugeordneten Werkzeuge und Verbrauchsmaterialien zurück"""
        try:
            # Basis-Query
            query = """
                SELECT 
                    REPLACE(key, 'category_', '') as name,
                    value,
                    description as usage,
                    (SELECT COUNT(*) FROM tools WHERE category = settings.value AND deleted = 0) as tools_count,
                    (SELECT COUNT(*) FROM consumables WHERE category = settings.value AND deleted = 0) as consumables_count
                FROM settings
                WHERE key LIKE 'category_%'
            """
            
            # Füge Verwendungszweck-Filter hinzu
            if usage == 'tools':
                query += " AND (description = 'tools' OR description = 'both')"
            elif usage == 'consumables':
                query += " AND (description = 'consumables' OR description = 'both')"
            
            query += " ORDER BY value"
            
            categories = cls.query(query)
            return [
                {
                    'name': cat['value'],
                    'usage': cat['usage'],
                    'tools_count': cat['tools_count'],
                    'consumables_count': cat['consumables_count']
                }
                for cat in categories
            ]
        except Exception as e:
            logging.error(f"Fehler beim Laden der Kategorien: {str(e)}")
            return []
    
    @classmethod
    def close_connection(cls):
        """Schließt die aktuelle Datenbankverbindung"""
        if hasattr(g, 'db'):
            try:
                g.db.close()
                delattr(g, 'db')
            except Exception as e:
                logger.error(f"Fehler beim Schließen der Datenbankverbindung: {str(e)}")
    
    @classmethod
    def restore_backup(cls, backup_file):
        """Stellt ein Backup wieder her"""
        try:
            # Schließe alle bestehenden Verbindungen
            if hasattr(cls, '_connection'):
                cls._connection.close()
                delattr(cls, '_connection')
            
            backup_path = os.path.join(Config.BACKUP_DIR, backup_file)
            if not os.path.exists(backup_path):
                print(f"Backup {backup_file} nicht gefunden")
                return False

            # Sichere aktuelle Datenbank
            db_path = Config.DATABASE
            if os.path.exists(db_path):
                os.rename(db_path, db_path + '.bak')

            # Kopiere Backup
            shutil.copy2(backup_path, db_path)

            # Teste die wiederhergestellte Datenbank
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Prüfe Tabelleneinträge
                tables = ['tools', 'consumables', 'workers', 'lendings', 'consumable_usages']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                    count = cursor.fetchone()['count']
                    print(f"Tabelle {table} enthält {count} Einträge")
                
                conn.close()
                
                # Lösche Backup wenn Test erfolgreich
                if os.path.exists(db_path + '.bak'):
                    os.remove(db_path + '.bak')
                    
                print("Backup wurde erfolgreich wiederhergestellt")
                
                # Erstelle Flag für Neustart
                tmp_dir = os.path.join(os.path.dirname(Config.BASE_DIR), 'tmp')
                os.makedirs(tmp_dir, exist_ok=True)
                with open(os.path.join(tmp_dir, 'needs_restart'), 'w') as f:
                    f.write('1')
                    
                return True

            except Exception as e:
                print(f"Fehler beim Testen des Backups: {str(e)}")
                # Stelle Original wieder her
                if os.path.exists(db_path + '.bak'):
                    os.remove(db_path)
                    os.rename(db_path + '.bak', db_path)
                return False

        except Exception as e:
            print(f"Fehler bei der Backup-Wiederherstellung: {str(e)}")
            return False

    @classmethod
    def init_app(cls, app):
        """Initialisiert die Datenbankverbindung für die Flask-App"""
        @app.teardown_appcontext
        def close_db(error):
            cls.close_connection()

class BaseModel:
    """Basisklasse für alle Datenbankmodelle"""
    TABLE_NAME = None
    
    @classmethod
    def get_all_active(cls):
        """Gibt alle aktiven (nicht gelöschten) Einträge zurück"""
        return Database.query(f"SELECT * FROM {cls.TABLE_NAME} WHERE deleted = 0")
    
    @classmethod
    def get_by_id(cls, id):
        """Gibt einen Eintrag anhand seiner ID zurück"""
        return Database.query(
            f"SELECT * FROM {cls.TABLE_NAME} WHERE id = ? AND deleted = 0", 
            [id], 
            one=True
        )
    
    @classmethod
    def get_by_barcode(cls, barcode):
        """Gibt einen Eintrag anhand seines Barcodes zurück"""
        return Database.query(
            f"SELECT * FROM {cls.TABLE_NAME} WHERE barcode = ? AND deleted = 0", 
            [barcode], 
            one=True
        )

def init_db():
    """Initialisiert die Datenbank"""
    # Hole die Konfiguration
    from app.config import config
    current_config = config['default']()
    
    # Verbindung herstellen
    conn = sqlite3.connect(current_config.DATABASE)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        
        # Werkzeuge
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        # Sync-Status
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_sync TIMESTAMP,
                last_attempt TIMESTAMP,
                status TEXT,
                error TEXT
            )
        ''')

        # Einstellungen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT
            )
        ''')

        # Sync-Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changes_count INTEGER NOT NULL,
                details TEXT
            )
        ''')

        conn.commit()
        logging.info("Datenbankschema erfolgreich initialisiert!")
        
    except Exception as e:
        logging.error(f"Fehler bei der Datenbankinitialisierung: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()