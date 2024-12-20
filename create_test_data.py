import sqlite3
import os
import sys
from datetime import datetime, timedelta
import random

# Füge das Hauptverzeichnis zum Python-Path hinzu
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.models.database import Database

def create_test_data():
    try:
        # Erst sicherstellen, dass die Datenbank und Tabellen existieren
        Database.init_db()
        
        conn = Database.get_db_connection()
        cursor = conn.cursor()
            
        # Test-Mitarbeiter erstellen
        workers = [
            ('W474598', 'Paula', 'Neumann', 'Technik'),
            ('W713866', 'Lisa', 'Koch', 'Service'),
            ('W399475', 'Max', 'Becker', 'Technik'),
            ('W210998', 'Ben', 'Weber', 'Mitarbeiter'),
            ('W304268', 'Clara', 'Schwarz', 'Mitarbeiter')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO workers 
            (barcode, firstname, lastname, department, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', workers)

        # Test-Werkzeuge erstellen
        tools = [
            ('T171871', 'Hammer 228', 'Standardhammer', 'Verfügbar'),
            ('T874690', 'Hammer 809', 'Großer Hammer', 'Verfügbar'),
            ('T449859', 'Hammer 619', 'Kleiner Hammer', 'Ausgeliehen'),
            ('T576474', 'Bohrmaschine 548', 'Bosch Professional', 'Ausgeliehen'),
            ('T236730', 'Wasserwaage 78', 'Präzisionswasserwaage', 'Verfügbar')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO tools 
            (barcode, name, description, status, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', tools)

        # Test-Verbrauchsmaterialien erstellen
        consumables = [
            ('C437350', 'Schrauben 330', 'Schrauben 4x30', 100),
            ('C394800', 'Reinigungstücher 416', 'Reinigungstücher', 200),
            ('C181554', 'Kabel 919', 'Kabel 2.5mm²', 50),
            ('C338844', 'Handschuhe 801', 'Arbeitshandschuhe Gr. L', 100),
            ('C525638', 'Schleifpapier 857', 'Schleifpapier K80', 75)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO consumables 
            (barcode, name, description, quantity)
            VALUES (?, ?, ?, ?)
        ''', consumables)

        # Einige Verbrauchsmaterial-Nutzungen
        cursor.execute("""
            INSERT INTO consumable_usages (consumable_barcode, worker_barcode, quantity)
            SELECT 
                c.barcode,
                w.barcode,
                ABS(RANDOM() % 10) + 1
            FROM consumables c
            CROSS JOIN workers w
            LIMIT 50
        """)

        conn.commit()
        print("Testdaten erfolgreich erstellt!")

    except sqlite3.Error as e:
        print(f"SQLite Fehler: {str(e)}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {str(e)}")
        raise e

if __name__ == "__main__":
    create_test_data() 