import sqlite3
import os
from datetime import datetime, timedelta
import random

def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'inventory.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_test_data():
    try:
        with get_db_connection() as conn:
            # Test-Mitarbeiter erstellen
            workers = [
                ('W001', 'Max', 'Mustermann'),
                ('W002', 'Anna', 'Schmidt'),
                ('W003', 'Peter', 'Meyer'),
                ('W004', 'Lisa', 'Weber'),
                ('W005', 'Klaus', 'Fischer')
            ]
            
            conn.executemany('''
                INSERT INTO workers (barcode, name, lastname, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', workers)

            # Test-Werkzeuge erstellen
            tools = [
                ('T001', 'Hammer', 'Standardhammer 300g', 'Werkzeugschrank 1', 'verfügbar'),
                ('T002', 'Schraubendreher Set', 'Phillips und Schlitz', 'Werkzeugschrank 2', 'verfügbar'),
                ('T003', 'Bohrmaschine', 'Bosch Professional', 'Werkzeugschrank 1', 'ausgeliehen'),
                ('T004', 'Säge', 'Handsäge 500mm', 'Werkzeugschrank 3', 'verfügbar'),
                ('T005', 'Zange', 'Kombizange 180mm', 'Werkzeugschrank 2', 'defekt')
            ]
            
            conn.executemany('''
                INSERT INTO tools (barcode, name, description, location, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', tools)

            # Test-Verbrauchsmaterial erstellen
            consumables = [
                ('C001', 'Schrauben 4x30', 'Schrauben', 'Lager A1', 500, 'Stück', 100),
                ('C002', 'Dübel 8mm', 'Dübel', 'Lager A2', 200, 'Stück', 50),
                ('C003', 'Klebeband', 'Verbrauchsmaterial', 'Lager B1', 30, 'Rollen', 10),
                ('C004', 'Arbeitshandschuhe', 'Schutzausrüstung', 'Lager C1', 45, 'Paar', 20),
                ('C005', 'Schleifpapier', 'Verbrauchsmaterial', 'Lager B2', 15, 'Bögen', 25)
            ]
            
            conn.executemany('''
                INSERT INTO consumables (barcode, bezeichnung, typ, ort, bestand, einheit, mindestbestand, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', consumables)

            # Einige Werkzeug-Ausleihen erstellen
            current_time = datetime.now()
            lendings = [
                ('T003', 'W001', current_time - timedelta(days=1), None),  # Noch ausgeliehen
                ('T001', 'W002', current_time - timedelta(days=3), current_time - timedelta(days=2)),  # Zurückgegeben
                ('T002', 'W003', current_time - timedelta(days=5), current_time - timedelta(days=4))   # Zurückgegeben
            ]
            
            conn.executemany('''
                INSERT INTO lendings (tool_barcode, worker_barcode, lending_time, return_time)
                VALUES (?, ?, ?, ?)
            ''', lendings)

            # Einige Werkzeug-Status-Änderungen
            tool_history = [
                ('T003', 'ausgeliehen', 'W001', current_time - timedelta(days=1)),
                ('T005', 'defekt', 'W003', current_time - timedelta(days=2)),
                ('T001', 'verfügbar', 'W002', current_time - timedelta(days=2))
            ]
            
            conn.executemany('''
                INSERT INTO tool_status_history (tool_barcode, action, worker_barcode, timestamp)
                VALUES (?, ?, ?, ?)
            ''', tool_history)

            # Einige Verbrauchsmaterial-Bewegungen
            consumables_history = [
                ('C001', 'entnahme', 'W001', -20, current_time - timedelta(days=1)),
                ('C002', 'entnahme', 'W002', -10, current_time - timedelta(days=2)),
                ('C003', 'nachbestellung', 'W003', 50, current_time - timedelta(days=3))
            ]
            
            conn.executemany('''
                INSERT INTO consumables_history (consumable_barcode, action, worker_barcode, quantity, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', consumables_history)

            conn.commit()
            print("Testdaten erfolgreich erstellt!")

    except sqlite3.IntegrityError as e:
        print(f"Fehler: Möglicherweise existieren einige Einträge bereits: {str(e)}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {str(e)}")

if __name__ == "__main__":
    create_test_data() 