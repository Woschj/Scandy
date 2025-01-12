from datetime import datetime, timedelta
from app.models.database import Database
from app.models.init_db import init_users
from werkzeug.security import generate_password_hash

def load_demo_data():
    """Lädt konsistente Demo-Daten in die Datenbank"""
    print("Lade Demo-Daten...")
    
    # Aktuelle Zeit für Timestamps
    current_time = datetime.now()
    one_day = timedelta(days=1)
    one_week = timedelta(weeks=1)
    
    with Database.get_db() as db:
        # Lösche existierende Daten außer users
        tables = ['settings', 'tools', 'consumables', 'workers', 'lendings', 'consumable_usages', 'tool_status_changes']
        for table in tables:
            db.execute(f"DELETE FROM {table}")
        
        # 1. Grundeinstellungen
        settings = [
            # Abteilungen
            ('department_APE', 'APE', 'Abteilung'),
            ('department_Kaufmännisches', 'Kaufmännisches', 'Abteilung'),
            ('department_Berufstrainer', 'Berufstrainer', 'Abteilung'),
            ('department_Medien', 'Medien und Digitales', 'Abteilung'),
            ('department_Service', 'Service', 'Abteilung'),
            
            # Kategorien für Werkzeuge
            ('category_Handwerkzeug', 'Handwerkzeug', 'Werkzeug-Kategorie'),
            ('category_Elektrowerkzeug', 'Elektrowerkzeug', 'Werkzeug-Kategorie'),
            ('category_Messwerkzeug', 'Messwerkzeug', 'Werkzeug-Kategorie'),
            ('category_Gartenwerkzeug', 'Gartenwerkzeug', 'Werkzeug-Kategorie'),
            ('category_Sicherheit', 'Sicherheitsausrüstung', 'Werkzeug-Kategorie'),
            
            # Kategorien für Verbrauchsmaterial
            ('category_Schrauben', 'Schrauben', 'Material-Kategorie'),
            ('category_Dübel', 'Dübel', 'Material-Kategorie'),
            ('category_Klebeband', 'Klebeband', 'Material-Kategorie'),
            ('category_Kabel', 'Kabel', 'Material-Kategorie'),
            ('category_Reinigung', 'Reinigungsmittel', 'Material-Kategorie'),
            
            # Lagerorte
            ('location_Werkstatt', 'Werkstatt', 'Lagerort'),
            ('location_Lager', 'Hauptlager', 'Lagerort'),
            ('location_Elektro', 'Elektrowerkstatt', 'Lagerort'),
            ('location_Garten', 'Gartenhaus', 'Lagerort'),
            ('location_Wagen', 'Werkzeugwagen', 'Lagerort')
        ]
        
        db.executemany(
            "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
            settings
        )
        
        # 2. Mitarbeiter
        workers = [
            ('W001', 'Max', 'Mustermann', 'APE', 'max.mustermann@firma.de'),
            ('W002', 'Lisa', 'Weber', 'Kaufmännisches', 'lisa.weber@firma.de'),
            ('W003', 'Peter', 'Schmidt', 'Berufstrainer', 'peter.schmidt@firma.de'),
            ('W004', 'Anna', 'Müller', 'Medien und Digitales', 'anna.mueller@firma.de'),
            ('W005', 'Thomas', 'Klein', 'Service', 'thomas.klein@firma.de'),
            ('W006', 'Sarah', 'Wagner', 'APE', 'sarah.wagner@firma.de'),
            ('W007', 'Michael', 'Bauer', 'Berufstrainer', 'michael.bauer@firma.de')
        ]
        
        for worker in workers:
            db.execute("""
                INSERT INTO workers (barcode, firstname, lastname, department, email, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (*worker, current_time, current_time))
        
        # 3. Werkzeuge
        tools = [
            ('T001', 'Hammer', 'Picard 300g Schlosserhammer', 'verfügbar', 'Handwerkzeug', 'Werkstatt'),
            ('T002', 'Akkuschrauber', 'Bosch GSR 18V-60 FC Professional', 'verfügbar', 'Elektrowerkzeug', 'Werkzeugwagen'),
            ('T003', 'Wasserwaage', 'Stabila 196-2 Digital 60cm', 'verfügbar', 'Messwerkzeug', 'Werkstatt'),
            ('T004', 'Kreissäge', 'Makita DHS680Z 18V', 'ausgeliehen', 'Elektrowerkzeug', 'Werkzeugwagen'),
            ('T005', 'Schraubendreher-Set', 'Wera Kraftform Kompakt 25', 'verfügbar', 'Handwerkzeug', 'Werkstatt'),
            ('T006', 'Multimeter', 'Fluke 175 True RMS', 'defekt', 'Messwerkzeug', 'Elektrowerkstatt'),
            ('T007', 'Rasenmäher', 'STIHL RMA 339 C', 'verfügbar', 'Gartenwerkzeug', 'Gartenhaus'),
            ('T008', 'Schweißhelm', 'ESAB Sentinel A50', 'verfügbar', 'Sicherheit', 'Werkstatt'),
            ('T009', 'Bandschleifer', 'Metabo BS 175', 'ausgeliehen', 'Elektrowerkzeug', 'Werkstatt'),
            ('T010', 'Laser-Entfernungsmesser', 'Bosch GLM 50 C', 'verfügbar', 'Messwerkzeug', 'Werkzeugwagen')
        ]
        
        for tool in tools:
            db.execute("""
                INSERT INTO tools (barcode, name, description, status, category, location, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (*tool, current_time, current_time))
        
        # 4. Verbrauchsmaterial
        consumables = [
            ('C001', 'Spax 4x30', 'Universalschrauben A2 200 Stk', 150, 100, 'Schrauben', 'Hauptlager'),
            ('C002', 'Spax 5x50', 'Universalschrauben A2 100 Stk', 75, 50, 'Schrauben', 'Hauptlager'),
            ('C003', 'Fischer SX 8x40', 'Nylon-Dübel 100 Stk', 200, 50, 'Dübel', 'Elektrowerkstatt'),
            ('C004', 'Isolierband', 'Schwarz 15mm x 10m', 25, 10, 'Klebeband', 'Werkstatt'),
            ('C005', 'NYM-J 3x1,5', 'Installationsleitung 50m', 5, 2, 'Kabel', 'Elektrowerkstatt'),
            ('C006', 'Reinigungstücher', 'Mehrzwecktücher 100 Stk', 80, 20, 'Reinigung', 'Hauptlager'),
            ('C007', 'WD-40', 'Multifunktionsöl 400ml', 12, 5, 'Reinigung', 'Werkstatt'),
            ('C008', 'Kabelbinder', 'UV-beständig 200x4.8mm 100 Stk', 300, 100, 'Kabel', 'Elektrowerkstatt')
        ]
        
        for consumable in consumables:
            db.execute("""
                INSERT INTO consumables (barcode, name, description, quantity, min_quantity, category, location, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*consumable, current_time, current_time))
        
        # 5. Ausleihen (aktuelle und vergangene)
        lendings = [
            # Aktuelle Ausleihen
            ('T004', 'W001', current_time - one_day, None),  # Max hat die Kreissäge
            ('T009', 'W006', current_time - timedelta(hours=4), None),  # Sarah hat den Bandschleifer
            
            # Vergangene Ausleihen (letzte Woche)
            ('T002', 'W003', current_time - one_week, current_time - one_week + timedelta(days=2)),
            ('T001', 'W002', current_time - one_week, current_time - one_week + timedelta(days=1)),
            ('T003', 'W004', current_time - one_week + timedelta(days=2), current_time - one_week + timedelta(days=3)),
            ('T005', 'W005', current_time - one_week + timedelta(days=3), current_time - one_week + timedelta(days=4)),
            
            # Vergangene Ausleihen (diese Woche)
            ('T007', 'W007', current_time - timedelta(days=3), current_time - timedelta(days=2)),
            ('T008', 'W001', current_time - timedelta(days=2), current_time - timedelta(days=1)),
            ('T010', 'W002', current_time - timedelta(days=1), current_time - timedelta(hours=2))
        ]
        
        for lending in lendings:
            db.execute("""
                INSERT INTO lendings (tool_barcode, worker_barcode, lent_at, returned_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
            """, (*lending, current_time))
        
        # 6. Materialverbrauch
        usages = [
            # Aktuelle Woche
            ('C001', 'W001', 25, current_time - timedelta(hours=4)),  # Max hat Schrauben verwendet
            ('C002', 'W006', 15, current_time - timedelta(hours=2)),  # Sarah hat Schrauben verwendet
            ('C003', 'W003', 30, current_time - timedelta(days=1)),   # Peter hat Dübel verwendet
            ('C004', 'W004', 2, current_time - timedelta(days=2)),    # Anna hat Isolierband verwendet
            
            # Letzte Woche
            ('C005', 'W005', 1, current_time - one_week + timedelta(days=1)),  # Thomas hat Kabel verwendet
            ('C006', 'W007', 10, current_time - one_week + timedelta(days=2)), # Michael hat Reinigungstücher verwendet
            ('C007', 'W002', 1, current_time - one_week + timedelta(days=3)),  # Lisa hat WD-40 verwendet
            ('C008', 'W001', 50, current_time - one_week + timedelta(days=4))  # Max hat Kabelbinder verwendet
        ]
        
        for usage in usages:
            db.execute("""
                INSERT INTO consumable_usages (consumable_barcode, worker_barcode, quantity, used_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
            """, (*usage, current_time))
            
        # 7. Werkzeug-Statusänderungen
        status_changes = [
            ('T006', 'verfügbar', 'defekt', 'Display zeigt falsche Werte an', current_time - timedelta(days=2)),
            ('T004', 'verfügbar', 'ausgeliehen', 'Reguläre Ausleihe', current_time - timedelta(days=1)),
            ('T009', 'verfügbar', 'ausgeliehen', 'Reguläre Ausleihe', current_time - timedelta(hours=4))
        ]
        
        for change in status_changes:
            db.execute("""
                INSERT INTO tool_status_changes (tool_barcode, old_status, new_status, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, change)
            
        db.commit()
        print(f"""
Demo-Daten wurden geladen:
- {len(settings)} Einstellungen
- {len(workers)} Mitarbeiter
- {len(tools)} Werkzeuge
- {len(consumables)} Verbrauchsmaterialien
- {len(lendings)} Ausleihen
- {len(usages)} Materialentnahmen
- {len(status_changes)} Statusänderungen
""") 