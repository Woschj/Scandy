import os
import sys
import sqlite3
from pathlib import Path

def get_database_path():
    """Gibt den Pfad zur Datenbank zurück"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'app', 'database', 'inventory.db')

def update_database():
    """Aktualisiert die Datenbankstruktur"""
    try:
        db_path = get_database_path()
        print(f"Verwende Datenbank: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Füge settings Tabelle hinzu...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Standard-Einstellungen
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
        
        conn.commit()
        print("Datenbankaktualisierung abgeschlossen!")
        conn.close()
        
    except Exception as e:
        print(f"Fehler: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    update_database() 