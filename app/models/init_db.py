from app.models.database import Database
from werkzeug.security import generate_password_hash

def init_db(db):
    """Erstellt alle notwendigen Tabellen"""
    # Werkzeuge
    db.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            location TEXT,
            status TEXT DEFAULT 'verfügbar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted INTEGER DEFAULT 0,
            deleted_at TIMESTAMP,
            sync_status TEXT DEFAULT 'pending'
        )
    ''')
    
    # Mitarbeiter
    db.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL UNIQUE,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted INTEGER DEFAULT 0,
            deleted_at TIMESTAMP,
            sync_status TEXT DEFAULT 'pending'
        )
    ''')
    
    # Verbrauchsmaterial
    db.execute('''
        CREATE TABLE IF NOT EXISTS consumables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            quantity INTEGER DEFAULT 0,
            min_quantity INTEGER DEFAULT 0,
            category TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted INTEGER DEFAULT 0,
            deleted_at TIMESTAMP,
            sync_status TEXT DEFAULT 'pending'
        )
    ''')
    
    # Ausleihen
    db.execute('''
        CREATE TABLE IF NOT EXISTS lendings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_barcode TEXT NOT NULL,
            worker_barcode TEXT NOT NULL,
            lent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            returned_at TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sync_status TEXT DEFAULT 'pending',
            FOREIGN KEY (tool_barcode) REFERENCES tools(barcode),
            FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
        )
    ''')
    
    # Verbrauchsmaterial-Nutzung
    db.execute('''
        CREATE TABLE IF NOT EXISTS consumable_usages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_barcode TEXT NOT NULL,
            worker_barcode TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sync_status TEXT DEFAULT 'pending',
            FOREIGN KEY (consumable_barcode) REFERENCES consumables(barcode),
            FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
        )
    ''')
    
    # Benutzer
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Einstellungen
    db.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        )
    ''')
    
    # Tickets
    db.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'offen',
            priority TEXT DEFAULT 'normal',
            created_by TEXT NOT NULL,
            assigned_to TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolution_notes TEXT,
            FOREIGN KEY (created_by) REFERENCES users (username),
            FOREIGN KEY (assigned_to) REFERENCES users (username)
        )
    ''')
    
    db.commit()

def init_users(app=None):
    """Initialisiert die Standardbenutzer"""
    try:
        if app is None:
            with Database.get_db() as db:
                init_db(db)  # Erstelle zuerst alle Tabellen
                _create_users(db)
        else:
            with app.app_context():
                with Database.get_db() as db:
                    init_db(db)  # Erstelle zuerst alle Tabellen
                    _create_users(db)
                    
    except Exception as e:
        print(f"Fehler beim Erstellen der Standardbenutzer: {str(e)}")
        raise

def _create_users(db):
    """Interne Funktion zum Erstellen der Benutzer"""
    # Lösche den alten Admin-User, falls vorhanden
    db.execute('DELETE FROM users WHERE username = ?', ['admin'])
    
    # Admin-Benutzer erstellen
    db.execute('''
        INSERT INTO users (username, password, role, is_admin)
        VALUES (?, ?, ?, ?)
    ''', [
        'Admin',
        generate_password_hash('BTZ-Scandy25', method='pbkdf2:sha256'),
        'admin',
        1
    ])

    # Prüfe ob die Techniker-Benutzer bereits existieren
    tech_ma = db.execute('SELECT id FROM users WHERE username = ?', ['TechnikMA']).fetchone()
    tech_tn = db.execute('SELECT id FROM users WHERE username = ?', ['TechnikTN']).fetchone()
    
    # Erstelle TechnikMA nur wenn noch nicht vorhanden
    if not tech_ma:
        db.execute('''
            INSERT INTO users (username, password, role, is_admin)
            VALUES (?, ?, ?, ?)
        ''', [
            'TechnikMA',
            generate_password_hash('BTZ-Admin', method='pbkdf2:sha256'),
            'admin',
            1
        ])

    # Erstelle TechnikTN nur wenn noch nicht vorhanden
    if not tech_tn:
        db.execute('''
            INSERT INTO users (username, password, role, is_admin)
            VALUES (?, ?, ?, ?)
        ''', [
            'TechnikTN',
            generate_password_hash('BTZ-Technik', method='pbkdf2:sha256'),
            'user',
            0
        ])
    
    db.commit()
    print("Standardbenutzer wurden erfolgreich erstellt")

if __name__ == '__main__':
    init_users() 