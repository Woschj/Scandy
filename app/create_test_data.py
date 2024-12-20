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
        conn = Database.get_db_connection()
        cursor = conn.cursor()
            
        # Abteilungen und andere Basisdaten definieren
        departments = [
            'Technik',
            'Service',
            'APE',
            'Medien und Digitales',
            'Kaufmännisches',
            'Mitarbeiter'
        ]

        locations = [
            'Werkstatt', 'Lager A', 'Lager B', 'Büro', 'Serverraum', 
            'Werkzeugraum', 'Elektronikwerkstatt', 'Holzwerkstatt'
        ]

        categories = {
            'tools': ['Handwerkzeug', 'Elektrowerkzeug', 'Messwerkzeug', 'Spezialwerkzeug', 'Gartenwerkzeug'],
            'consumables': ['Befestigungsmaterial', 'Elektromaterial', 'Reinigungsmaterial', 'Schutzmaterial', 'Verbrauchsteile']
        }

        # Test-Mitarbeiter erstellen (60 Mitarbeiter)
        first_names = ['Max', 'Anna', 'Paul', 'Lisa', 'Felix', 'Emma', 'Ben', 'Clara', 'David', 'Sophie',
                      'Ida', 'Jan', 'Laura', 'Noah', 'Mia', 'Oskar', 'Paula', 'Quentin', 'Rosa', 'Tim']
        last_names = ['Müller', 'Schmidt', 'Weber', 'Hoffmann', 'Koch', 'Becker', 'Klein', 'Schröder', 
                     'Neumann', 'Schwarz', 'Wagner', 'Schulz', 'Zimmermann']

        workers = []
        for i in range(60):
            barcode = f'W{random.randint(100000, 999999)}'
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            department = random.choice(departments)
            email = f"{first_name.lower()}.{last_name.lower()}@firma.de"
            workers.append((barcode, first_name, last_name, department, email))

        cursor.executemany('''
            INSERT OR IGNORE INTO workers 
            (barcode, firstname, lastname, department, email, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', workers)

        # Test-Werkzeuge erstellen (100 Werkzeuge)
        tool_types = ['Hammer', 'Bohrmaschine', 'Schraubendreher', 'Säge', 'Zange', 'Multimeter',
                     'Wasserwaage', 'Maßband', 'Schraubenschlüssel', 'Kreissäge', 'Bandschleifer']
        tool_status = ['Verfügbar', 'Ausgeliehen', 'Defekt']
        
        tools = []
        for i in range(100):
            barcode = f'T{random.randint(100000, 999999)}'
            tool_type = random.choice(tool_types)
            number = random.randint(1, 999)
            name = f'{tool_type} {number}'
            status = random.choice(tool_status)
            category = random.choice(categories['tools'])
            location = random.choice(locations)
            tools.append((barcode, name, f'Standard {tool_type}', status, category, location))

        cursor.executemany('''
            INSERT OR IGNORE INTO tools 
            (barcode, name, description, status, category, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', tools)

        # Test-Verbrauchsmaterialien erstellen (100 Materialien)
        consumable_types = [
            ('Schrauben', 'Stück', 1000),
            ('Dübel', 'Stück', 500),
            ('Kabel', 'Meter', 200),
            ('Klebeband', 'Rollen', 50),
            ('Batterien', 'Stück', 100),
            ('Handschuhe', 'Paar', 50),
            ('Reinigungstücher', 'Packung', 30),
            ('Schleifpapier', 'Blatt', 100),
            ('Lötdraht', 'Meter', 100),
            ('Kabelbinder', 'Stück', 500)
        ]

        consumables = []
        for i in range(100):
            barcode = f'C{random.randint(100000, 999999)}'
            cons_type, unit, max_quantity = random.choice(consumable_types)
            number = random.randint(1, 999)
            name = f'{cons_type} {number}'
            quantity = random.randint(0, max_quantity)
            min_quantity = max_quantity // 10
            category = random.choice(categories['consumables'])
            location = random.choice(locations)
            consumables.append((barcode, name, f'Standard {cons_type}', quantity, min_quantity, category, location))

        cursor.executemany('''
            INSERT OR IGNORE INTO consumables 
            (barcode, name, description, quantity, min_quantity, category, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', consumables)

        # Ausleihvorgänge erstellen (für ausgeliehene Werkzeuge)
        lent_tools = cursor.execute(
            "SELECT barcode FROM tools WHERE status = 'Ausgeliehen'"
        ).fetchall()
        
        worker_barcodes = [w[0] for w in cursor.execute("SELECT barcode FROM workers").fetchall()]
        
        for tool in lent_tools:
            # Zufälliges Ausleihdatum in den letzten 30 Tagen
            days_ago = random.randint(1, 30)
            lent_at = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute('''
                INSERT INTO lendings (tool_barcode, worker_barcode, lent_at)
                VALUES (?, ?, ?)
            ''', (tool[0], random.choice(worker_barcodes), lent_at.strftime('%Y-%m-%d %H:%M:%S')))

        # Verbrauchsmaterial-Nutzungen erstellen (50 Nutzungen)
        consumable_barcodes = [c[0] for c in cursor.execute("SELECT barcode FROM consumables").fetchall()]
        
        for _ in range(50):
            days_ago = random.randint(1, 30)
            used_at = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute('''
                INSERT INTO consumable_usages 
                (consumable_barcode, worker_barcode, quantity, used_at)
                VALUES (?, ?, ?, ?)
            ''', (
                random.choice(consumable_barcodes),
                random.choice(worker_barcodes),
                random.randint(1, 10),
                used_at.strftime('%Y-%m-%d %H:%M:%S')
            ))

        conn.commit()
        print("Testdaten erfolgreich erstellt!")

    except sqlite3.Error as e:
        print(f"SQLite Fehler: {str(e)}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {str(e)}")
        raise e

if __name__ == "__main__":
    create_test_data() 