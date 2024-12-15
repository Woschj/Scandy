import sqlite3
import random
import os
from app import DBConfig, get_db_connection
import logging
from datetime import datetime, timedelta
import traceback

# Absolute Pfade zu den Datenbanken
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKERS_DB = os.path.join(BASE_DIR, 'workers.db')
TOOLS_DB = os.path.join(BASE_DIR, 'lager.db')
LENDINGS_DB = os.path.join(BASE_DIR, 'lendings.db')
CONSUMABLES_DB = os.path.join(BASE_DIR, 'consumables.db')

def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    return datetime.fromisoformat(s)

# Registriere die Adapter am Anfang der Datei
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("DATETIME", convert_datetime)

def init_dbs():
    """Erstellt alle notwendigen Datenbanktabellen"""
    try:
        # Workers Database
        with sqlite3.connect(DBConfig.WORKERS_DB) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS workers (
                    barcode TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    lastname TEXT NOT NULL,
                    bereich TEXT,
                    email TEXT
                );
                
                CREATE TABLE IF NOT EXISTS workers_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_barcode TEXT NOT NULL,
                    action TEXT NOT NULL,
                    changed_fields TEXT,
                    changed_by TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                );
                
                CREATE TABLE IF NOT EXISTS deleted_workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_id INTEGER,
                    name TEXT NOT NULL,
                    lastname TEXT NOT NULL,
                    barcode TEXT NOT NULL,
                    bereich TEXT,
                    email TEXT,
                    deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    deleted_by TEXT
                );
            ''')
            
        # Tools Database
        with sqlite3.connect(DBConfig.TOOLS_DB) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS tools (
                    barcode TEXT PRIMARY KEY,
                    gegenstand TEXT NOT NULL,
                    ort TEXT DEFAULT 'Lager',
                    typ TEXT,
                    status TEXT DEFAULT 'Verfügbar',
                    image_path TEXT
                );
                
                CREATE TABLE IF NOT EXISTS tools_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_barcode TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT,
                    changed_fields TEXT,
                    changed_by TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_barcode) REFERENCES tools(barcode)
                );
                
                CREATE TABLE IF NOT EXISTS tool_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_barcode TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT,
                    comment TEXT,
                    changed_by TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_barcode) REFERENCES tools(barcode)
                );
                
                CREATE TABLE IF NOT EXISTS deleted_tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT NOT NULL,
                    gegenstand TEXT NOT NULL,
                    ort TEXT,
                    typ TEXT,
                    status TEXT,
                    deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    deleted_by TEXT
                );
            ''')
            
        # Consumables Database
        with sqlite3.connect(DBConfig.CONSUMABLES_DB) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS consumables (
                    barcode TEXT PRIMARY KEY,
                    bezeichnung TEXT NOT NULL,
                    ort TEXT DEFAULT 'Lager',
                    typ TEXT,
                    status TEXT DEFAULT 'Verfügbar',
                    mindestbestand INTEGER DEFAULT 0,
                    aktueller_bestand INTEGER DEFAULT 0,
                    einheit TEXT DEFAULT 'Stück',
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS consumables_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumable_barcode TEXT NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    old_stock INTEGER NOT NULL,
                    new_stock INTEGER NOT NULL,
                    changed_by TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consumable_barcode) REFERENCES consumables(barcode)
                );
                
                CREATE TABLE IF NOT EXISTS deleted_consumables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_id INTEGER,
                    barcode TEXT NOT NULL,
                    bezeichnung TEXT NOT NULL,
                    ort TEXT,
                    typ TEXT,
                    mindestbestand INTEGER,
                    letzter_bestand INTEGER,
                    einheit TEXT,
                    deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    deleted_by TEXT
                );
            ''')
            
        # Lendings Database
        with sqlite3.connect(DBConfig.LENDINGS_DB) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS lendings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_barcode TEXT NOT NULL,      -- Änderung hier: worker_barcode statt worker_name
                    item_barcode TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    checkout_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    return_time DATETIME,
                    amount INTEGER DEFAULT 1,
                    old_stock INTEGER,
                    new_stock INTEGER,
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                );
            ''')
            
        print("✓ Alle Datenbanken erfolgreich initialisiert")
        return True
        
    except Exception as e:
        print(f"✗ Fehler bei der Datenbankinitialisierung: {str(e)}")
        return False

def clear_existing_data():
    """Löscht alle vorhandenen Daten"""
    print("Lösche bestehende Daten...")
    try:
        # Tools DB
        with sqlite3.connect(DBConfig.TOOLS_DB) as conn:
            # Lösche alle Tabellen
            tables = ['tool_status_history', 'tools_history', 'deleted_tools', 'tools']
            for table in tables:
                try:
                    conn.execute(f'DROP TABLE IF EXISTS {table}')
                except Exception as e:
                    print(f"Info: Konnte Tabelle {table} nicht löschen: {str(e)}")
            conn.commit()
            print("✓ Tools DB zurückgesetzt")
            
        # Lendings DB
        with sqlite3.connect(DBConfig.LENDINGS_DB) as conn:
            conn.execute('DROP TABLE IF EXISTS lendings')
            conn.commit()
            print("✓ Lendings DB zurückgesetzt")
            
        # Consumables DB
        with sqlite3.connect(DBConfig.CONSUMABLES_DB) as conn:
            tables = ['consumables_history', 'deleted_consumables', 'consumables']
            for table in tables:
                try:
                    conn.execute(f'DROP TABLE IF EXISTS {table}')
                except Exception as e:
                    print(f"Info: Konnte Tabelle {table} nicht löschen: {str(e)}")
            conn.commit()
            print("✓ Consumables DB zurückgesetzt")
            
        # Workers DB
        with sqlite3.connect(DBConfig.WORKERS_DB) as conn:
            tables = ['deleted_workers', 'workers']
            for table in tables:
                try:
                    conn.execute(f'DROP TABLE IF EXISTS {table}')
                except Exception as e:
                    print(f"Info: Konnte Tabelle {table} nicht löschen: {str(e)}")
            conn.commit()
            print("✓ Workers DB zurückgesetzt")
            
        print("\n✓ Alle Datenbanken erfolgreich zurückgesetzt")
        return True
            
    except Exception as e:
        print(f"✗ Fehler beim Zurücksetzen der Datenbanken: {str(e)}")
        return False

def check_if_empty(conn, table_name):
    """Prüft ob eine Tabelle leer ist"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    return count == 0

def create_random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def create_test_data():
    try:
        # Hole alle Worker-Barcodes
        with get_db_connection(DBConfig.WORKERS_DB) as conn:
            workers = [row['barcode'] for row in 
                      conn.execute("SELECT barcode FROM workers").fetchall()]
            
            if not workers:
                print("Keine Mitarbeiter in der Datenbank gefunden!")
                return False
        
        # Lendings mit korrekten Datetime-Konvertern
        with sqlite3.connect(DBConfig.LENDINGS_DB, 
                           detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.row_factory = sqlite3.Row
            all_lendings = []
            
            # Werkzeug-Ausleihen
            with get_db_connection(DBConfig.TOOLS_DB) as tool_conn:
                tools = [row['barcode'] for row in 
                        tool_conn.execute("SELECT barcode FROM tools WHERE status = 'Ausgeliehen'").fetchall()]
                
                for tool_barcode in tools:
                    worker_barcode = random.choice(workers)
                    days_ago = random.randint(1, 30)
                    checkout_date = datetime.now() - timedelta(days=days_ago)
                    
                    all_lendings.append((
                        worker_barcode,
                        tool_barcode,
                        'tool',
                        checkout_date,
                        None,  # return_time
                        1,     # amount
                        None,  # old_stock
                        None   # new_stock
                    ))
            
            # Füge alle Ausleihen ein
            if all_lendings:
                conn.executemany('''
                    INSERT INTO lendings 
                    (worker_barcode, item_barcode, item_type, checkout_time, 
                     return_time, amount, old_stock, new_stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', all_lendings)
                conn.commit()
                print(f"✓ {len(all_lendings)} Ausleih-Testdaten erfolgreich eingefügt")
            else:
                print("Keine Werkzeuge zum Ausleihen gefunden")

    except Exception as e:
        print(f"\n✗ FEHLER beim Erstellen der Testdaten: {str(e)}")
        print(traceback.format_exc())
        return False
    
    return True

def create_test_tools():
    """Erstellt realistische Werkzeug-Testdaten"""
    tools = [
        # Handwerkzeuge
        ('HW001', 'Hammer 300g', 'Handwerkzeug', 'Verfügbar'),
        ('HW002', 'Schraubendreher Set Phillips', 'Handwerkzeug', 'Verfügbar'),
        ('HW003', 'Wasserpumpenzange 250mm', 'Handwerkzeug', 'Ausgeliehen'),
        ('HW004', 'Maßband 5m', 'Handwerkzeug', 'Verfügbar'),
        ('HW005', 'Wasserwaage 60cm', 'Handwerkzeug', 'Ausgeliehen'),
        
        # Elektrowerkzeuge
        ('EW001', 'Bosch Akkuschrauber GSR 18V', 'Elektrowerkzeug', 'Verfügbar'),
        ('EW002', 'Makita Bohrhammer DHR243', 'Elektrowerkzeug', 'Ausgeliehen'),
        ('EW003', 'DeWalt Stichsäge DW331K', 'Elektrowerkzeug', 'Verfügbar'),
        ('EW004', 'Milwaukee Winkelschleifer M18', 'Elektrowerkzeug', 'Defekt'),
        ('EW005', 'Hilti Meißelhammer TE 500', 'Elektrowerkzeug', 'Ausgeliehen'),
        
        # Messwerkzeuge
        ('MW001', 'Digitaler Messschieber 150mm', 'Messwerkzeug', 'Verfügbar'),
        ('MW002', 'Laser-Entfernungsmesser', 'Messwerkzeug', 'Ausgeliehen'),
        ('MW003', 'Multimeter Fluke 179', 'Messwerkzeug', 'Verfügbar'),
        ('MW004', 'Wärmebildkamera FLIR E4', 'Messwerkzeug', 'Defekt'),
        ('MW005', 'Schallpegelmesser PCE-322A', 'Messwerkzeug', 'Verfügbar'),
        
        # Spezialwerkzeuge
        ('SW001', 'Drehmomentschlüssel 40-200Nm', 'Spezialwerkzeug', 'Verfügbar'),
        ('SW002', 'Hydraulikpresse 20t', 'Spezialwerkzeug', 'Ausgeliehen'),
        ('SW003', 'Schweißgerät MIG/MAG', 'Spezialwerkzeug', 'Verfügbar'),
        ('SW004', 'Druckluft-Nietpistole', 'Spezialwerkzeug', 'Defekt'),
        ('SW005', 'Rohrreinigungsspirale 20m', 'Spezialwerkzeug', 'Ausgeliehen')
    ]
    
    try:
        with get_db_connection(DBConfig.TOOLS_DB) as conn:
            conn.executemany('''
                INSERT INTO tools (barcode, gegenstand, typ, status)
                VALUES (?, ?, ?, ?)
            ''', tools)
            conn.commit()
            print(f"✓ {len(tools)} Werkzeug-Testdaten erfolgreich eingefügt")
            
            # Füge Einträge in tools_history für defekte Werkzeuge ein
            defect_tools = [(t[0], t[1]) for t in tools if t[3] == 'Defekt']
            for barcode, name in defect_tools:
                conn.execute('''
                    INSERT INTO tool_status_history 
                    (tool_barcode, old_status, new_status, comment, changed_by)
                    VALUES (?, 'Verfügbar', 'Defekt', ?, 'System')
                ''', (barcode, f"Testdaten: {name} als defekt markiert"))
            conn.commit()
            
    except Exception as e:
        print(f"✗ Fehler beim Einfügen der Werkzeug-Testdaten: {str(e)}")
        return False
    return True

def create_test_consumables():
    """Erstellt realistische Verbrauchsmaterial-Testdaten"""
    consumables = [
        # Holzbearbeitung (HB)
        ('HB001', 'Schleifpapier 80er Körnung', 'Holzbearbeitung', 50, 200, 'Blatt'),
        ('HB002', 'Schleifpapier 120er Körnung', 'Holzbearbeitung', 50, 150, 'Blatt'),
        ('HB003', 'Schleifpapier 240er Körnung', 'Holzbearbeitung', 50, 180, 'Blatt'),
        ('HB004', 'Holzschrauben 4x40mm', 'Holzbearbeitung', 100, 500, 'Stück'),
        ('HB005', 'Holzleim wasserfest 250ml', 'Holzbearbeitung', 2, 8, 'Flasche'),
        ('HB006', 'Holzdübel 8mm', 'Holzbearbeitung', 50, 200, 'Stück'),
        ('HB007', 'Spanplattenschrauben 5x60', 'Holzbearbeitung', 100, 400, 'Stück'),
        
        # Metallbearbeitung (MB)
        ('MB001', 'Bohrer HSS 1-10mm Set', 'Metallbearbeitung', 1, 5, 'Set'),
        ('MB002', 'Gewindebohrer M6', 'Metallbearbeitung', 2, 6, 'Stück'),
        ('MB003', 'Schneidöl 1L', 'Metallbearbeitung', 1, 4, 'Flasche'),
        ('MB004', 'Trennscheiben 125mm', 'Metallbearbeitung', 10, 50, 'Stück'),
        ('MB005', 'Schutzhandschuhe Gr. L', 'Metallbearbeitung', 5, 20, 'Paar'),
        ('MB006', 'Schweißdraht 0.8mm', 'Metallbearbeitung', 1, 4, 'Rolle'),
        ('MB007', 'Schleifscheiben K80 125mm', 'Metallbearbeitung', 10, 40, 'Stück'),
        
        # 3D-Druck (3D)
        ('3D001', 'PLA Filament schwarz', '3D-Druck', 1, 5, 'Rolle'),
        ('3D002', 'PLA Filament weiß', '3D-Druck', 1, 5, 'Rolle'),
        ('3D003', 'PETG Filament transparent', '3D-Druck', 1, 3, 'Rolle'),
        ('3D004', 'TPU Filament flexibel', '3D-Druck', 1, 2, 'Rolle'),
        ('3D005', 'Druckbett-Kleber', '3D-Druck', 1, 4, 'Stick'),
        ('3D006', 'Isopropanol 99%', '3D-Druck', 1, 3, 'Liter'),
        
        # Allgemein (AL)
        ('AL001', 'Einweghandschuhe Nitril L', 'Allgemein', 2, 10, 'Packung'),
        ('AL002', 'Papiertücher', 'Allgemein', 5, 20, 'Rolle'),
        ('AL003', 'Schutzbrille klar', 'Allgemein', 5, 15, 'Stück'),
        ('AL004', 'Gehörschutz', 'Allgemein', 3, 10, 'Stück'),
        ('AL005', 'Staubmaske FFP2', 'Allgemein', 10, 50, 'Stück')
    ]
    
    try:
        with get_db_connection(DBConfig.CONSUMABLES_DB) as conn:
            # Füge Verbrauchsmaterialien ein
            for barcode, bezeichnung, typ, mindest, aktuell, einheit in consumables:
                conn.execute('''
                    INSERT INTO consumables 
                    (barcode, bezeichnung, typ, mindestbestand, aktueller_bestand, einheit)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (barcode, bezeichnung, typ, mindest, aktuell, einheit))
            
            conn.commit()
            print(f"✓ {len(consumables)} Verbrauchsmaterial-Testdaten erfolgreich eingefügt")
            
    except Exception as e:
        print(f"✗ Fehler beim Einfügen der Verbrauchsmaterial-Testdaten: {str(e)}")
        return False
    return True

def create_test_workers():
    """Erstellt realistische Mitarbeiter-Testdaten"""
    workers = [
        # Werkstattleitung
        ('MA001', 'Thomas', 'Weber', 'Werkstattleitung', 'thomas.weber@werkstatt.de'),
        ('MA002', 'Sandra', 'Müller', 'Werkstattleitung', 'sandra.mueller@werkstatt.de'),
        
        # Holzwerkstatt
        ('MA010', 'Michael', 'Schneider', 'Holzwerkstatt', 'michael.schneider@werkstatt.de'),
        ('MA011', 'Julia', 'Wagner', 'Holzwerkstatt', 'julia.wagner@werkstatt.de'),
        ('MA012', 'Frank', 'Hoffmann', 'Holzwerkstatt', 'frank.hoffmann@werkstatt.de'),
        
        # Metallwerkstatt
        ('MA020', 'Andreas', 'Schmidt', 'Metallwerkstatt', 'andreas.schmidt@werkstatt.de'),
        ('MA021', 'Petra', 'Koch', 'Metallwerkstatt', 'petra.koch@werkstatt.de'),
        ('MA022', 'Markus', 'Bauer', 'Metallwerkstatt', 'markus.bauer@werkstatt.de'),
        
        # Elektrowerkstatt
        ('MA030', 'Stefan', 'Fischer', 'Elektrowerkstatt', 'stefan.fischer@werkstatt.de'),
        ('MA031', 'Laura', 'Meyer', 'Elektrowerkstatt', 'laura.meyer@werkstatt.de'),
        
        # 3D-Druck & Digital
        ('MA040', 'Daniel', 'Klein', '3D-Druck', 'daniel.klein@werkstatt.de'),
        ('MA041', 'Sarah', 'Neumann', '3D-Druck', 'sarah.neumann@werkstatt.de'),
        
        # Auszubildende
        ('MA090', 'Tim', 'Lehmann', 'Holzwerkstatt', 'tim.lehmann@werkstatt.de'),
        ('MA091', 'Lisa', 'Krause', 'Metallwerkstatt', 'lisa.krause@werkstatt.de'),
        ('MA092', 'Jan', 'Richter', 'Elektrowerkstatt', 'jan.richter@werkstatt.de'),
        
        # Teilzeitkräfte
        ('MA095', 'Marie', 'Wolf', 'Holzwerkstatt', 'marie.wolf@werkstatt.de'),
        ('MA096', 'Oliver', 'Schröder', 'Metallwerkstatt', 'oliver.schroeder@werkstatt.de'),
        
        # Lager & Logistik
        ('MA100', 'Christian', 'Berger', 'Lager', 'christian.berger@werkstatt.de'),
        ('MA101', 'Nicole', 'Schwarz', 'Lager', 'nicole.schwarz@werkstatt.de')
    ]
    
    try:
        with get_db_connection(DBConfig.WORKERS_DB) as conn:
            # Füge Mitarbeiter ein
            conn.executemany('''
                INSERT INTO workers 
                (barcode, name, lastname, bereich, email)
                VALUES (?, ?, ?, ?, ?)
            ''', workers)
            
            conn.commit()
            print(f"✓ {len(workers)} Mitarbeiter-Testdaten erfolgreich eingefügt")
            
    except Exception as e:
        print(f"✗ Fehler beim Einfügen der Mitarbeiter-Testdaten: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    print("=== DATENBANK RESET UND INITIALISIERUNG ===")
    print("\nLösche alte Daten...")
    clear_existing_data()
    
    print("\nInitialisiere Datenbanken...")
    if init_dbs():
        print("\nErstelle neue Testdaten...")
        if create_test_workers() and create_test_tools() and create_test_consumables():
            create_test_data()
            print("\n✓ Prozess erfolgreich abgeschlossen")
        else:
            print("\n✗ Fehler beim Erstellen der Testdaten")
    else:
        print("\n✗ Fehler bei der Datenbankinitialisierung") 