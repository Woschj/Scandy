from flask import g, current_app
import sqlite3
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class Database:
    @staticmethod
    def get_database_path():
        if os.environ.get('RENDER') == 'true':
            return os.path.join('/opt/render/project/src/database', 'inventory.db')
        else:
            return os.path.join('database', 'inventory.db')
    
    DATABASE_PATH = property(get_database_path)

    @staticmethod
    def get_db():
        if 'db' not in g:
            db_path = Database.get_database_path()
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
        return g.db

    @staticmethod
    def get_db_connection():
        """Direkter Datenbankzugriff für Verwaltungsaufgaben"""
        conn = sqlite3.connect(Database.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        """Initialisiert die Datenbank wenn sie nicht existiert"""
        if not os.path.exists(Database.DATABASE_PATH):
            with Database.get_db() as conn:
                cursor = conn.cursor()
                # Hier SQL für Tabellenerstellung
                cursor.execute('''CREATE TABLE IF NOT EXISTS...''')

    @staticmethod
    def close_db():
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @staticmethod
    def query(sql, params=(), one=False):
        try:
            db = Database.get_db()
            cur = db.execute(sql, params)
            rv = cur.fetchall()
            db.commit()
            return (rv[0] if rv else None) if one else rv
        except sqlite3.Error as e:
            db.rollback()
            raise Exception(f"Datenbankfehler: {str(e)}")

    @staticmethod
    def init_db():
        """Initialisiert die Datenbankstruktur"""
        if not os.path.exists('database'):
            os.makedirs('database')
            
        conn = Database.get_db_connection()
        cursor = conn.cursor()

        # Werkzeuge (Tools)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'verfügbar',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0
            )
        ''')

        # Verbrauchsmaterialien (Consumables)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0
            )
        ''')

        # Mitarbeiter (Workers)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                department TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0
            )
        ''')

        # Ausleihvorgänge (Lendings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lendings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_barcode TEXT,
                worker_barcode TEXT,
                lent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                returned_at TIMESTAMP,
                FOREIGN KEY (tool_barcode) REFERENCES tools (barcode),
                FOREIGN KEY (worker_barcode) REFERENCES workers (barcode)
            )
        ''')

        # System-Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                message TEXT,
                details TEXT
            )
        ''')

        # Settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

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

def init_db():
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