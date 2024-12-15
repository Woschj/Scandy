import sqlite3
import os
from flask import g
from datetime import datetime

class DBConfig:
    DATABASE_PATH = os.path.join('database', 'inventory.db')

def get_db(database_name='inventory.db'):
    """Datenbankverbindung herstellen oder aus Cache zurückgeben"""
    db_path = os.path.join('database', database_name)
    
    if 'db' not in g:
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db

def get_db_connection():
    """Stellt eine Verbindung zur Datenbank her"""
    return sqlite3.connect('database/inventory.db')

def init_db():
    conn = get_db_connection()
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

    conn.commit()
    conn.close()

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

__all__ = ['init_database', 'get_db', 'get_db_connection', 'close_db', 'show_db_structure', 'DBConfig']

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