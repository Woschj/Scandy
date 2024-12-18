import os
import sqlite3
import random
from datetime import datetime, timedelta

# Stelle sicher, dass der database Ordner existiert
database_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
if not os.path.exists(database_path):
    os.makedirs(database_path)

# Verbindung zur Datenbank mit absolutem Pfad
db_path = os.path.join(database_path, 'inventory.db')
print(f"Verwende Datenbank: {db_path}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Bestehende Daten löschen
print("Lösche bestehende Daten...")
cur.execute('DELETE FROM lendings')
cur.execute('DELETE FROM tools')
cur.execute('DELETE FROM consumables')
cur.execute('DELETE FROM workers')

# Vordefinierte Listen für realistische Daten
tool_categories = ["Handwerkzeug", "Elektrowerkzeug", "Messwerkzeug", "Spezialwerkzeug", "Gartenwerkzeug"]
tool_names = [
    "Akkuschrauber", "Hammer", "Schraubendreher", "Zange", "Säge", "Bohrmaschine", 
    "Schleifmaschine", "Messgerät", "Multimeter", "Lötkolben", "Schraubenschlüssel",
    "Wasserwaage", "Maßband", "Kreissäge", "Stichsäge", "Bandschleifer"
]

tool_locations = ["Werkstatt A", "Werkstatt B", "Lager 1", "Lager 2", "Werkzeugschrank", "Regal 1"]

consumable_names = [
    "Schrauben", "Muttern", "Dübel", "Klebeband", "Kabel", "Lötzinn", 
    "Schleifpapier", "Handschuhe", "Schutzbrille", "Batterien", "Reinigungstücher"
]

consumable_categories = ["Befestigung", "Elektro", "Schutzausrüstung", "Verbrauch", "Werkzeugzubehör"]
consumable_locations = ["Lager A", "Lager B", "Schrank 1", "Schrank 2", "Regal A", "Regal B"]

departments = [
    "Medien und Digitales", "Technik", "Kaufmännisches", "Service", "APE", "Mitarbeiter"
]

first_names = [
    "Anna", "Ben", "Clara", "David", "Emma", "Felix", "Greta", "Hans", "Ida", "Jan",
    "Karl", "Lisa", "Max", "Nina", "Otto", "Paula", "Quentin", "Rosa", "Stefan", "Tina"
]

last_names = [
    "Müller", "Schmidt", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", 
    "Koch", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann"
]

# Hilfsfunktionen
def generate_barcode(prefix):
    return f"{prefix}{random.randint(100000, 999999)}"

def random_date(start_date, end_date):
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

# Werkzeuge generieren
print("Generiere Werkzeuge...")
for i in range(100):
    name = f"{random.choice(tool_names)} {random.randint(1, 999)}"
    barcode = generate_barcode('T')
    location = random.choice(tool_locations)
    # Erstmal alle Werkzeuge als verfügbar erstellen
    status = 'Verfügbar'
    
    cur.execute('''
        INSERT INTO tools (name, barcode, location, status, 
                          created_at, deleted, description, category)
        VALUES (?, ?, ?, ?, datetime('now'), 0, ?, ?)
    ''', (name, barcode, location, status, 
          f"Beschreibung für {name}", random.choice(tool_categories)))

def format_datetime(dt):
    """Rundet datetime auf Sekunden"""
    return dt.replace(microsecond=0)

# Verbrauchsmaterial generieren
print("Generiere Verbrauchsmaterial...")
for i in range(100):
    name = f"{random.choice(consumable_names)} {random.randint(1, 999)}"
    barcode = generate_barcode('C')
    category = random.choice(consumable_categories)
    location = random.choice(consumable_locations)
    quantity = random.randint(0, 100)
    min_quantity = random.randint(10, 30)
    
    cur.execute('''
        INSERT INTO consumables (name, barcode, category, location, quantity, min_quantity, 
                                created_at, deleted, description)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 0, ?)
    ''', (name, barcode, category, location, quantity, min_quantity,
          f"Beschreibung für {name}"))

# Mitarbeiter generieren
print("Generiere Mitarbeiter...")
for i in range(60):
    firstname = random.choice(first_names)
    lastname = random.choice(last_names)
    barcode = generate_barcode('W')
    department = random.choice(departments)
    email = f"{firstname.lower()}.{lastname.lower()}@firma.de"
    
    cur.execute('''
        INSERT INTO workers (firstname, lastname, barcode, department, email,
                           created_at, deleted)
        VALUES (?, ?, ?, ?, ?, datetime('now'), 0)
    ''', (firstname, lastname, barcode, department, email,
          ))

# Einige Ausleihen generieren
print("Generiere Ausleihen...")
# Hole alle Worker-Barcodes
cur.execute('SELECT barcode FROM workers')
worker_barcodes = [row[0] for row in cur.fetchall()]

# Hole alle Tool-Barcodes
cur.execute('SELECT barcode FROM tools')
tool_barcodes = [row[0] for row in cur.fetchall()]

# Verhindern dass ein Werkzeug mehrfach ausgeliehen wird
borrowed_tools = set()

# Generiere 200 zufällige Ausleihen
for i in range(200):
    worker_barcode = random.choice(worker_barcodes)
    # Wähle nur Werkzeuge die noch nicht ausgeliehen sind
    available_tools = [t for t in tool_barcodes if t not in borrowed_tools]
    if not available_tools:
        continue
    tool_barcode = random.choice(available_tools)
    borrowed_tools.add(tool_barcode)
    
    lent_at = format_datetime(random_date(datetime.now() - timedelta(days=90), datetime.now()))
    
    # 70% Chance, dass das Item zurückgegeben wurde
    if random.random() < 0.7:
        returned_at = format_datetime(random_date(lent_at, datetime.now()))
        # Setze Status auf Verfügbar
        cur.execute('UPDATE tools SET status = ? WHERE barcode = ?', 
                    ('Verfügbar', tool_barcode))
        # Werkzeug kann wieder ausgeliehen werden
        borrowed_tools.remove(tool_barcode)
    else:
        returned_at = None
        # Setze Status auf Ausgeliehen
        cur.execute('UPDATE tools SET status = ? WHERE barcode = ?', 
                    ('Ausgeliehen', tool_barcode))
    
    cur.execute('''
        INSERT INTO lendings (worker_barcode, tool_barcode, lent_at, returned_at)
        VALUES (?, ?, ?, ?)
    ''', (worker_barcode, tool_barcode, lent_at, returned_at))

# Setze einige Werkzeuge auf Defekt (10%)
print("Setze einige Werkzeuge auf Defekt...")
cur.execute('SELECT barcode FROM tools WHERE status = ?', ('Verfügbar',))
available_tools = [row[0] for row in cur.fetchall()]
defect_count = len(available_tools) // 10  # 10% der verfügbaren Werkzeuge

for barcode in random.sample(available_tools, defect_count):
    cur.execute('UPDATE tools SET status = ? WHERE barcode = ?',
                ('Defekt', barcode))

# Prüfe die Konsistenz der Daten
print("\nPrüfe Datenkonsistenz...")

# Prüfe ob ausgeliehene Werkzeuge auch einen Ausleiher haben
cur.execute('''
    SELECT t.barcode, t.name 
    FROM tools t 
    WHERE t.status = 'Ausgeliehen' 
    AND NOT EXISTS (
        SELECT 1 FROM lendings l 
        WHERE l.tool_barcode = t.barcode 
        AND l.returned_at IS NULL
    )
''')
inconsistent = cur.fetchall()
if inconsistent:
    print("Warnung: Folgende Werkzeuge sind als ausgeliehen markiert, haben aber keine aktive Ausleihe:")
    for barcode, name in inconsistent:
        print(f"- {name} ({barcode})")

# Änderungen speichern
conn.commit()
conn.close()

print("Testdaten erfolgreich generiert!")

def create_tables():
    """Erstellt die benötigten Tabellen"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            department TEXT NOT NULL,
            deleted INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consumable_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consumable_id) REFERENCES consumables(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'available',
            location TEXT,
            category TEXT,
            deleted INTEGER DEFAULT 0
        )
    ''')