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
        """Stellt sicher, dass die Datenbank existiert"""
        logging.info("=== CHECKING DATABASE AT STARTUP ===")
        
        # Config-Instanz erstellen
        from app.config import config
        current_config = config['default']()
        db_path = current_config.DATABASE
        
        logging.info(f"Configured database path: {db_path}")
        
        # Absoluten Pfad ermitteln
        db_dir = os.path.dirname(db_path)
        
        logging.info(f"Absolute database path: {os.path.abspath(db_path)}")
        
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(db_dir, exist_ok=True)
        
        if os.path.exists(db_path):
            logging.info("Datenbank existiert bereits")
        else:
            logging.info("Erstelle neue Datenbank")
            conn = sqlite3.connect(db_path)
            conn.close()
    
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
            g.db = cls.get_db_connection()
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
        try:
            logging.info("\n=== DATABASE QUERY ===")
            logging.info(f"SQL: {sql}")
            logging.info(f"Parameters: {params}")
            
            conn = Database.get_db_connection()
            cursor = conn.cursor()
            
            if params is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
            
            results = cursor.fetchall()
            
            if results:
                logging.info(f"Number of results: {len(results)}")
                logging.info(f"Example record: {dict(results[0])}")
            else:
                logging.info("No results returned")
            
            conn.close()
            return (results[0] if results else None) if one else results
            
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
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