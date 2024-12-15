import os
import sqlite3
from pathlib import Path

# Pfad zur Datenbank (jetzt im database Ordner)
DB_PATH = Path(__file__).parent.parent.parent / 'database' / 'inventory.db'

# Pfad zum SQL Script
SQL_PATH = Path(__file__).parent.parent / 'sql' / 'design_settings.sql'

def setup_design_settings():
    print(f"Verwende Datenbank: {DB_PATH}")
    
    # Stelle sicher, dass der database Ordner existiert
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # Verbinde zur Datenbank
    with sqlite3.connect(DB_PATH) as conn:
        # Lese und führe das SQL Script aus
        with open(SQL_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        
        # Überprüfe, ob die Tabelle erstellt wurde
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'").fetchone()
        if result:
            print("Settings-Tabelle wurde erfolgreich erstellt!")
            # Zeige die eingetragenen Werte
            settings = conn.execute("SELECT * FROM settings").fetchall()
            print("\nAktuelle Einstellungen:")
            for key, value in settings:
                print(f"{key}: {value}")
        else:
            print("Fehler: Settings-Tabelle wurde nicht erstellt!")

if __name__ == '__main__':
    setup_design_settings()