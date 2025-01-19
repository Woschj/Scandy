import logging
from werkzeug.security import generate_password_hash
from app.models.database import Database

class SchemaManager:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.logger.info("SchemaManager initialisiert")

    def init_schema(self):
        """Initialisiert das Datenbankschema"""
        try:
            conn = self.db.get_db_connection()
            cursor = conn.cursor()
            
            # Access Settings Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_settings (
                    route TEXT PRIMARY KEY,
                    is_public BOOLEAN DEFAULT 0,
                    description TEXT
                )
            ''')
            
            # Standard-Einstellungen
            default_settings = [
                ('tools.index', 1, 'Werkzeug-Übersicht'),
                ('tools.details', 1, 'Werkzeug-Details'),
                ('consumables.index', 1, 'Verbrauchsmaterial-Übersicht'),
                ('consumables.details', 1, 'Verbrauchsmaterial-Details'),
                ('workers.index', 0, 'Mitarbeiter-Übersicht'),
                ('workers.details', 0, 'Mitarbeiter-Details'),
                ('admin.dashboard', 0, 'Admin-Dashboard'),
                ('admin.trash', 0, 'Papierkorb'),
                ('history.view', 0, 'Verlauf'),
                ('tickets.index', 0, 'Ticket-System'),
                ('tickets.create', 0, 'Ticket erstellen'),
                ('tickets.edit', 0, 'Ticket bearbeiten')
            ]
            
            # Füge Standardeinstellungen ein
            cursor.executemany('''
                INSERT OR IGNORE INTO access_settings (route, is_public, description)
                VALUES (?, ?, ?)
            ''', default_settings)
            
            conn.commit()
            self.logger.info("Zugriffseinstellungen initialisiert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren des Schemas: {e}")
            conn.rollback()
        finally:
            conn.close()
        
    def init_settings(self):
        """Initialisiert die Grundeinstellungen in der Datenbank"""
        default_settings = {
            'theme': 'light',
            'language': 'de',
            'items_per_page': '10',
            'primary_color': '259 94% 51%',    # Standard Blau
            'secondary_color': '314 100% 47%',  # Standard Pink
            'accent_color': '174 60% 51%'       # Standard Türkis
        }
        
        try:
            conn = self.db.get_db_connection()
            cursor = conn.cursor()
            
            for key, value in default_settings.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO settings (key, value)
                    VALUES (?, ?)
                """, (key, value))
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren der Einstellungen: {e}")
            conn.rollback()
        finally:
            conn.close()
        
    def reset_schema(self):
        """Löscht und erstellt das Schema neu"""
        try:
            conn = self.db.get_db_connection()
            cursor = conn.cursor()
            
            # Vorsicht: Dies löscht alle Daten!
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            
            conn.commit()
            self.init_schema()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Zurücksetzen des Schemas: {e}")
            conn.rollback()
        finally:
            conn.close()
        
    def init_tables(self):
        """Initialisiert alle Tabellen"""
        self.logger.info("Starte init_tables()")
        conn = self.db.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Tools Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    location TEXT,
                    status TEXT DEFAULT 'verfügbar',
                    last_maintenance DATE,
                    next_maintenance DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0
                )
            ''')
            
            # Workers Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    department TEXT,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0
                )
            ''')
            
            # Consumables Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consumables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    location TEXT,
                    quantity INTEGER DEFAULT 0,
                    min_quantity INTEGER DEFAULT 0,
                    unit TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0
                )
            ''')
            
            # Lendings Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lendings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_barcode TEXT NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    lent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_at TIMESTAMP,
                    returned_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (tool_barcode) REFERENCES tools(barcode),
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                )
            ''')
            
            # Settings Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT
                )
            ''')
            
            # History Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    user_id INTEGER,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Consumable Usage Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consumable_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumable_id INTEGER NOT NULL,
                    worker_barcode TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consumable_id) REFERENCES consumables(id),
                    FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
                )
            ''')
            
            # Tickets Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'offen',
                    priority TEXT DEFAULT 'normal',
                    created_by TEXT NOT NULL,
                    assigned_to TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(username),
                    FOREIGN KEY (assigned_to) REFERENCES users(username)
                )
            ''')
            
            # Ticket Comments Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
                    FOREIGN KEY (created_by) REFERENCES users(username)
                )
            ''')
            
            # Berechtigungstabellen
            self.logger.info("Erstelle permissions Tabelle")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT
                )
            ''')
            
            self.logger.info("Erstelle roles Tabelle")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT
                )
            ''')
            
            self.logger.info("Erstelle role_permissions Tabelle")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id INTEGER,
                    permission_id INTEGER,
                    PRIMARY KEY (role_id, permission_id),
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(id)
                )
            ''')
            
            self.logger.info("Erstelle user_roles Tabelle")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER,
                    role_id INTEGER,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            ''')
            
            self.logger.info("Erstelle user_permissions Tabelle")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_permissions (
                    user_id INTEGER,
                    permission_id INTEGER,
                    PRIMARY KEY (user_id, permission_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(id)
                )
            ''')
            
            self.logger.info("Commit der Tabellenänderungen")
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Tabellen: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_users_table(self):
        """Initialisiert die Users-Tabelle"""
        self.logger.info("Starte init_users_table()")
        with Database.get_db() as conn:
            cursor = conn.cursor()
            
            self.logger.info("Erstelle users Tabelle")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.logger.info("Erstelle user_permissions Tabelle")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_permissions (
                    user_id INTEGER,
                    permission_id INTEGER,
                    PRIMARY KEY (user_id, permission_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(id)
                )
            ''')
            
            # Standard Admin-Account erstellen
            self.logger.info("Prüfe ob Admin-Account existiert")
            admin_exists = cursor.execute(
                'SELECT 1 FROM users WHERE username = ?', 
                ['admin']
            ).fetchone()
            
            if not admin_exists:
                self.logger.info("Erstelle Admin-Account")
                cursor.execute('''
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                ''', [
                    'admin',
                    generate_password_hash('admin'),
                    'admin'
                ])
            
            self.logger.info("Commit der User-Änderungen")
            conn.commit()