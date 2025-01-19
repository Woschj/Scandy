"""
Datenbank-Konfiguration und Verbindungsmanagement
----------------------------------------------

Dieses Modul verwaltet die SQLite-Datenbankverbindung und stellt grundlegende Datenbankfunktionen bereit.

Hauptfunktionen:
1. Datenbankverbindung aufbauen und verwalten
2. Verbindungspool für mehrere Threads bereitstellen
3. Automatisches Schließen von Verbindungen
4. Fehlerbehandlung bei Datenbankoperationen

Datenbankstruktur:
- inventory.db: Hauptdatenbank
  - tools: Werkzeuge und deren Status
  - workers: Mitarbeiterinformationen
  - consumables: Verbrauchsmaterialien
  - lending: Ausleihvorgänge
  - history: Verlauf aller Aktionen

Sicherheitsmerkmale:
- Automatische Transaktion für jede Anfrage
- Prepared Statements gegen SQL-Injection
- Backup vor kritischen Operationen

Verwendung:
- Von allen Model-Klassen verwendet
- Über get_db() Funktion zugreifen
- Automatisches Schließen am Ende jeder Anfrage
"""

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

class UserDatabase:
    """Separate Datenbankklasse für die Benutzerverwaltung"""
    
    @classmethod
    def get_db(cls):
        """Gibt eine Verbindung zur Benutzer-Datenbank zurück"""
        if 'user_db' not in g:
            db_path = os.path.join(Config.DATABASE_DIR, 'users.db')
            g.user_db = sqlite3.connect(db_path)
            g.user_db.row_factory = sqlite3.Row
        return g.user_db
    
    @classmethod
    def close_db(cls):
        """Schließt die Benutzer-Datenbankverbindung"""
        db = g.pop('user_db', None)
        if db is not None:
            db.close()

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
            
            # Automatisches Commit für INSERT, UPDATE, DELETE
            if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
                logging.info("Änderungen committed")
                
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
                    s.value as name,
                    COUNT(w.id) as worker_count
                FROM settings s
                LEFT JOIN workers w ON w.department = s.value AND w.deleted = 0
                WHERE s.key LIKE 'department_%'
                AND s.value IS NOT NULL 
                AND s.value != ''
                GROUP BY s.value
                ORDER BY s.value
            """)
            
            return [{'name': dept['name'], 'worker_count': dept['worker_count']} for dept in departments]
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
                    s.value as name,
                    s.description as usage,
                    (SELECT COUNT(*) FROM tools WHERE location = s.value AND deleted = 0) as tools_count,
                    (SELECT COUNT(*) FROM consumables WHERE location = s.value AND deleted = 0) as consumables_count
                FROM settings s
                WHERE s.key LIKE 'location_%'
                AND s.value IS NOT NULL 
                AND s.value != ''
            """
            
            # Füge Verwendungszweck-Filter hinzu
            if usage == 'tools':
                query += " AND (s.description = 'tools' OR s.description = 'both')"
            elif usage == 'consumables':
                query += " AND (s.description = 'consumables' OR s.description = 'both')"
            
            query += " ORDER BY s.value"
            
            locations = cls.query(query)
            return [
                {
                    'name': loc['name'],
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
                    s.value as name,
                    s.description as usage,
                    (SELECT COUNT(*) FROM tools WHERE category = s.value AND deleted = 0) as tools_count,
                    (SELECT COUNT(*) FROM consumables WHERE category = s.value AND deleted = 0) as consumables_count
                FROM settings s
                WHERE s.key LIKE 'category_%'
                AND s.value IS NOT NULL 
                AND s.value != ''
            """
            
            # Füge Verwendungszweck-Filter hinzu
            if usage == 'tools':
                query += " AND (s.description = 'tools' OR s.description = 'both')"
            elif usage == 'consumables':
                query += " AND (s.description = 'consumables' OR s.description = 'both')"
            
            query += " ORDER BY s.value"
            
            categories = cls.query(query)
            return [
                {
                    'name': cat['name'],
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

    @classmethod
    def update_category_usage(cls, name, usage):
        """Aktualisiert die Nutzungsart einer Kategorie"""
        try:
            with cls.get_db() as db:
                db.execute(
                    "UPDATE settings SET description = ? WHERE key = ? AND key LIKE 'category_%'",
                    (usage, f"category_{name}")
                )
                db.commit()
                return True
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Kategorie-Nutzung: {e}")
            return False

    @classmethod
    def update_location_usage(cls, name, usage):
        """Aktualisiert die Nutzungsart eines Standorts"""
        try:
            with cls.get_db() as db:
                db.execute(
                    "UPDATE settings SET description = ? WHERE key = ? AND key LIKE 'location_%'",
                    (usage, f"location_{name}")
                )
                db.commit()
                return True
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Standort-Nutzung: {e}")
            return False

    @classmethod
    def get_consumables_forecast(cls):
        """Berechnet die Bestandsprognose für Verbrauchsmaterialien"""
        try:
            return cls.query("""
                WITH daily_usage AS (
                    SELECT 
                        c.barcode,
                        c.name,
                        c.quantity as current_amount,
                        CAST(SUM(cu.quantity) AS FLOAT) / 30 as avg_daily_usage
                    FROM consumables c
                    LEFT JOIN consumable_usages cu 
                        ON c.barcode = cu.consumable_barcode
                        AND cu.used_at >= date('now', '-30 days')
                    WHERE c.deleted = 0
                    GROUP BY c.barcode, c.name, c.quantity
                )
                SELECT 
                    name,
                    current_amount,
                    ROUND(avg_daily_usage, 2) as avg_daily_usage,
                    CASE 
                        WHEN avg_daily_usage > 0 
                        THEN ROUND(current_amount / avg_daily_usage)
                        ELSE 999
                    END as days_remaining
                FROM daily_usage
                WHERE current_amount > 0
                ORDER BY days_remaining ASC
                LIMIT 10
            """)
        except Exception as e:
            print(f"Fehler beim Abrufen der Bestandsprognose: {e}")
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
    """Initialisiert die Datenbank und stellt sicher, dass alle Tabellen existieren"""
    with Database.get_db() as conn:
        cursor = conn.cursor()
        
        # Prüfe und erstelle die Tabellen
        tables = {
            'tools': '''
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    location TEXT,
                    status TEXT DEFAULT 'verfügbar',
                    last_maintenance DATE,
                    next_maintenance DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0
                )
            ''',
            'workers': '''
                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    firstname TEXT NOT NULL,
                    lastname TEXT NOT NULL,
                    department TEXT,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0
                )
            ''',
            'consumables': '''
                CREATE TABLE IF NOT EXISTS consumables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    location TEXT,
                    quantity INTEGER DEFAULT 0,
                    min_quantity INTEGER DEFAULT 0,
                    unit TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0
                )
            ''',
            'lendings': '''
                CREATE TABLE IF NOT EXISTS lendings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_barcode TEXT NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    lent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_at TIMESTAMP,
                    returned_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (tool_barcode) REFERENCES tools(barcode),
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                )
            ''',
            'settings': '''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT
                )
            ''',
            'history': '''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    user_id INTEGER,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'consumable_usages': '''
                CREATE TABLE IF NOT EXISTS consumable_usages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumable_barcode TEXT NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consumable_barcode) REFERENCES consumables(barcode),
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                )
            ''',
            'tool_status_changes': '''
                CREATE TABLE IF NOT EXISTS tool_status_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_barcode TEXT NOT NULL,
                    old_status TEXT NOT NULL,
                    new_status TEXT NOT NULL,
                    reason TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_barcode) REFERENCES tools(barcode)
                )
            ''',
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'tickets': '''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'offen',
                    priority TEXT DEFAULT 'normal',
                    created_by TEXT NOT NULL,
                    assigned_to TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(username),
                    FOREIGN KEY (assigned_to) REFERENCES users(username)
                )
            ''',
            'ticket_comments': '''
                CREATE TABLE IF NOT EXISTS ticket_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
                    FOREIGN KEY (created_by) REFERENCES users(username)
                )
            ''',
            'ticket_notes': '''
                CREATE TABLE IF NOT EXISTS ticket_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    note TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
                    FOREIGN KEY (created_by) REFERENCES users(username)
                )
            '''
        }
        
        # Erstelle alle Tabellen
        for table_name, create_sql in tables.items():
            try:
                cursor.execute(create_sql)
                logging.info(f"Tabelle {table_name} wurde überprüft/erstellt")
            except Exception as e:
                logging.error(f"Fehler beim Erstellen der Tabelle {table_name}: {str(e)}")
        
        # Commit die Änderungen
        conn.commit()
        logging.info("Datenbank-Initialisierung abgeschlossen")