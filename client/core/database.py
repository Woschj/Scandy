import sqlite3
import os
from pathlib import Path

class LocalDatabase:
    def __init__(self):
        """Initialisiert die lokale Datenbank"""
        self.db_path = self._get_db_path()
        self._ensure_db_exists()
        
    def _get_db_path(self):
        """Ermittelt den Pfad zur Datenbank"""
        # Datenbank im Benutzerverzeichnis speichern
        app_dir = Path.home() / '.scandy'
        app_dir.mkdir(exist_ok=True)
        return app_dir / 'inventory.db'
        
    def _ensure_db_exists(self):
        """Stellt sicher, dass die Datenbank existiert"""
        if not self.db_path.exists():
            self._create_db()
            
    def _create_db(self):
        """Erstellt die Datenbank mit allen Tabellen"""
        with sqlite3.connect(self.db_path) as conn:
            # Werkzeuge
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

            # Benutzer
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )
            ''')
            
    def query(self, sql, params=None, one=False):
        """Führt eine Datenbankabfrage aus"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                    
                if one:
                    return cursor.fetchone()
                return cursor.fetchall()
                
            except Exception as e:
                print(f"Datenbankfehler: {str(e)}")
                raise 