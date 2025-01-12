from datetime import datetime, timedelta
from .database import Database

def load_demo_data():
    """Lädt Testdaten in die Datenbank"""
    conn = Database.get_db()
    cursor = conn.cursor()

    # Lösche vorhandene Daten
    tables = ['settings', 'tools', 'consumables', 'workers', 'lendings', 'consumable_usages', 'users']
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')

    # Kategorien
    categories = [
        ('category_1', 'Handwerkzeuge', 'tools'),
        ('category_2', 'Elektrowerkzeuge', 'tools'),
        ('category_3', 'Schrauben', 'consumables'),
        ('category_4', 'Dübel', 'consumables'),
        ('category_5', 'Messgeräte', 'both'),
        ('category_6', 'Sägen', 'tools'),
        ('category_7', 'Bohrer', 'consumables'),
        ('category_8', 'Schutzausrüstung', 'both'),
        ('category_9', 'Schleifmittel', 'consumables'),
        ('category_10', 'Schweißzubehör', 'both')
    ]
    
    cursor.executemany(
        'INSERT INTO settings (key, value, description) VALUES (?, ?, ?)',
        categories
    )

    # Standorte
    locations = [
        ('location_1', 'Werkstatt', 'Hauptstandort'),
        ('location_2', 'Elektrowerkstatt', 'Elektroarbeiten'),
        ('location_3', 'Lager', 'Materialien'),
        ('location_4', 'Außenlager', 'Großgeräte'),
        ('location_5', 'Büro', 'Verwaltung'),
        ('location_6', 'Schweißerei', 'Schweißarbeiten'),
        ('location_7', 'Metallwerkstatt', 'Metallbearbeitung'),
        ('location_8', 'Holzwerkstatt', 'Holzbearbeitung')
    ]
    
    cursor.executemany(
        'INSERT INTO settings (key, value, description) VALUES (?, ?, ?)',
        locations
    )

    # Abteilungen
    departments = [
        ('department_1', 'Mechanik', 'Mechanische Werkstatt'),
        ('department_2', 'Elektrik', 'Elektrische Installationen'),
        ('department_3', 'Wartung', 'Instandhaltung'),
        ('department_4', 'Ausbildung', 'Lehrlinge'),
        ('department_5', 'Metallbau', 'Metallverarbeitung'),
        ('department_6', 'Schweißerei', 'Schweißarbeiten'),
        ('department_7', 'Holzbau', 'Holzverarbeitung')
    ]
    
    cursor.executemany(
        'INSERT INTO settings (key, value, description) VALUES (?, ?, ?)',
        departments
    )

    # Werkzeuge
    tools = [
        ('T001', 'Bosch Akkuschrauber', 'GSR 18V-28, 18 Volt', 'Elektrowerkzeuge', 'Werkstatt', 'verfügbar'),
        ('T002', 'Hammer', 'Fäustel 1000g', 'Handwerkzeuge', 'Werkstatt', 'verfügbar'),
        ('T003', 'Multimeter', 'Fluke 179', 'Messgeräte', 'Elektrowerkstatt', 'ausgeliehen'),
        ('T004', 'Schlagbohrmaschine', 'Hilti TE 30', 'Elektrowerkzeuge', 'Werkstatt', 'defekt'),
        ('T005', 'Wasserwaage', '60cm Digital', 'Messgeräte', 'Lager', 'verfügbar'),
        ('T006', 'Kreissäge', 'Makita 5008MG', 'Sägen', 'Holzwerkstatt', 'verfügbar'),
        ('T007', 'Schweißgerät', 'EWM Pico 160', 'Schweißzubehör', 'Schweißerei', 'ausgeliehen'),
        ('T008', 'Bandschleifer', 'Metabo BS 175', 'Elektrowerkzeuge', 'Metallwerkstatt', 'verfügbar'),
        ('T009', 'Stichsäge', 'Bosch PST 800 PEL', 'Sägen', 'Holzwerkstatt', 'defekt'),
        ('T010', 'Drehmomentschlüssel', '20-100 Nm', 'Handwerkzeuge', 'Werkstatt', 'verfügbar'),
        ('T011', 'Lasermessgerät', 'Bosch GLM 50 C', 'Messgeräte', 'Lager', 'verfügbar'),
        ('T012', 'Winkelschleifer', 'Makita GA5040C', 'Elektrowerkzeuge', 'Metallwerkstatt', 'ausgeliehen'),
        ('T013', 'Schraubstock', '150mm', 'Handwerkzeuge', 'Werkstatt', 'verfügbar'),
        ('T014', 'Plasmaschneidgerät', 'Hypertherm 45XP', 'Schweißzubehör', 'Schweißerei', 'defekt'),
        ('T015', 'Standbohrmaschine', 'Optimum B24H', 'Elektrowerkzeuge', 'Metallwerkstatt', 'verfügbar')
    ]
    
    for barcode, name, description, category, location, status in tools:
        cursor.execute('''
            INSERT INTO tools 
            (barcode, name, description, category, location, status, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (barcode, name, description, category, location, status, 
              datetime.now(), datetime.now()))

    # Verbrauchsmaterial
    consumables = [
        ('C001', 'Spax 4x40', 'Universalschrauben 200 Stk', 'Schrauben', 'Lager', 100, 50),
        ('C002', 'Spax 5x60', 'Universalschrauben 100 Stk', 'Schrauben', 'Lager', 25, 50),
        ('C003', 'Fischer SX 8x40', 'Nylon-Dübel 100 Stk', 'Dübel', 'Elektrowerkstatt', 75, 50),
        ('C004', 'Fischer UX 6x35', 'Universal-Dübel 200 Stk', 'Dübel', 'Lager', 150, 100),
        ('C005', 'HSS Bohrer 6mm', 'Spiralbohrer 10 Stk', 'Bohrer', 'Metallwerkstatt', 45, 30),
        ('C006', 'Holzbohrer-Set', '3-10mm 8-teilig', 'Bohrer', 'Holzwerkstatt', 15, 20),
        ('C007', 'Schweißelektroden', 'E6013 2.5mm 1kg', 'Schweißzubehör', 'Schweißerei', 80, 50),
        ('C008', 'Schleifscheiben', 'K80 125mm 50 Stk', 'Schleifmittel', 'Metallwerkstatt', 120, 60),
        ('C009', 'Arbeitshandschuhe', 'Größe 9 10 Paar', 'Schutzausrüstung', 'Lager', 35, 40),
        ('C010', 'Schleifpapier', 'K120 230x280mm 100 Stk', 'Schleifmittel', 'Holzwerkstatt', 200, 100),
        ('C011', 'Schweißdraht', '0.8mm 5kg', 'Schweißzubehör', 'Schweißerei', 40, 30),
        ('C012', 'Schutzbrille', 'Klar 5 Stk', 'Schutzausrüstung', 'Lager', 18, 25)
    ]
    
    for barcode, name, description, category, location, quantity, min_quantity in consumables:
        cursor.execute('''
            INSERT INTO consumables 
            (barcode, name, description, category, location, quantity, min_quantity, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (barcode, name, description, category, location, quantity, min_quantity,
              datetime.now(), datetime.now()))

    # Mitarbeiter
    workers = [
        ('W001', 'Max', 'Mustermann', 'Mechanik', 'Ausbilder'),
        ('W002', 'Anna', 'Schmidt', 'Elektrik', 'Fachkraft'),
        ('W003', 'Peter', 'Weber', 'Wartung', 'Techniker'),
        ('W004', 'Lisa', 'Meyer', 'Ausbildung', 'Azubi'),
        ('W005', 'Thomas', 'Wagner', 'Metallbau', 'Meister'),
        ('W006', 'Sarah', 'Koch', 'Schweißerei', 'Fachkraft'),
        ('W007', 'Michael', 'Bauer', 'Holzbau', 'Geselle'),
        ('W008', 'Julia', 'Fischer', 'Ausbildung', 'Azubi'),
        ('W009', 'Andreas', 'Schulz', 'Mechanik', 'Geselle'),
        ('W010', 'Laura', 'Hoffmann', 'Elektrik', 'Meisterin')
    ]
    
    for barcode, firstname, lastname, department, role in workers:
        cursor.execute('''
            INSERT INTO workers 
            (barcode, firstname, lastname, department, role, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (barcode, firstname, lastname, department, role,
              datetime.now(), datetime.now()))

    # Ausleihen (aktuelle und vergangene)
    current_time = datetime.now()
    lendings = [
        # Aktuelle Ausleihen
        ('T003', 'W002', current_time - timedelta(days=1), None),  # Multimeter ausgeliehen von Elektriker
        ('T007', 'W006', current_time - timedelta(hours=4), None),  # Schweißgerät ausgeliehen von Schweißer
        ('T012', 'W005', current_time - timedelta(hours=2), None),  # Winkelschleifer ausgeliehen von Metallbauer
        
        # Vergangene Ausleihen
        ('T001', 'W004', current_time - timedelta(days=5), current_time - timedelta(days=4)),
        ('T002', 'W001', current_time - timedelta(days=3), current_time - timedelta(days=2)),
        ('T006', 'W007', current_time - timedelta(days=2), current_time - timedelta(days=1)),
        ('T008', 'W009', current_time - timedelta(days=4), current_time - timedelta(days=3)),
        ('T010', 'W003', current_time - timedelta(days=6), current_time - timedelta(days=5)),
        ('T011', 'W002', current_time - timedelta(days=7), current_time - timedelta(days=6))
    ]
    
    for tool_barcode, worker_barcode, lent_at, returned_at in lendings:
        cursor.execute('''
            INSERT INTO lendings 
            (tool_barcode, worker_barcode, lent_at, returned_at)
            VALUES (?, ?, ?, ?)
        ''', (tool_barcode, worker_barcode, lent_at, returned_at))

    # Materialverbrauch
    usages = [
        # Aktuelle Woche
        ('C001', 'W001', 20, current_time - timedelta(hours=4)),
        ('C002', 'W002', 15, current_time - timedelta(hours=6)),
        ('C003', 'W003', 25, current_time - timedelta(hours=8)),
        ('C007', 'W006', 10, current_time - timedelta(hours=3)),
        ('C008', 'W005', 30, current_time - timedelta(hours=5)),
        
        # Letzte Woche
        ('C001', 'W009', 15, current_time - timedelta(days=3)),
        ('C004', 'W002', 40, current_time - timedelta(days=4)),
        ('C005', 'W005', 12, current_time - timedelta(days=5)),
        ('C009', 'W004', 5, current_time - timedelta(days=6)),
        ('C010', 'W007', 25, current_time - timedelta(days=7)),
        
        # Ältere Einträge
        ('C002', 'W001', 30, current_time - timedelta(days=10)),
        ('C003', 'W003', 20, current_time - timedelta(days=12)),
        ('C006', 'W007', 8, current_time - timedelta(days=14)),
        ('C011', 'W006', 15, current_time - timedelta(days=15)),
        ('C012', 'W010', 10, current_time - timedelta(days=16))
    ]
    
    for consumable_barcode, worker_barcode, quantity, used_at in usages:
        cursor.execute('''
            INSERT INTO consumable_usages 
            (consumable_barcode, worker_barcode, quantity, used_at)
            VALUES (?, ?, ?, ?)
        ''', (consumable_barcode, worker_barcode, quantity, used_at))

    # Admin-Benutzer
    cursor.execute('''
        INSERT INTO users (username, password)
        VALUES (?, ?)
    ''', ('admin', 'pbkdf2:sha256:600000$dNGJfZxKjYxjcFgF$6b6f1d3d397c60e2a7494a5d3c33184d91f4d3f4f2c1b41e60f2669b6f25d4a1'))

    conn.commit()
    
    print("Demo-Daten wurden geladen:")
    print(f"- {len(tools)} Werkzeuge")
    print(f"- {len(consumables)} Verbrauchsmaterialien")
    print(f"- {len(workers)} Mitarbeiter")
    print(f"- {len(lendings)} Ausleihen")
    print(f"- {len(usages)} Materialentnahmen")
    print(f"- {len(categories)} Kategorien")
    print(f"- {len(locations)} Standorte")
    print(f"- {len(departments)} Abteilungen") 