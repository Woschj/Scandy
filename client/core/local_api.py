from werkzeug.security import check_password_hash, generate_password_hash

class LocalAPI:
    def __init__(self, db):
        self.db = db
        
    def login(self, username, password):
        """Benutzer anmelden"""
        user = self.db.query(
            'SELECT * FROM users WHERE username = ?',
            [username],
            one=True
        )
        
        if user and check_password_hash(user['password'], password):
            return True
        return False
        
    def setup(self, username, password):
        """Ersteinrichtung durchführen"""
        try:
            # Users-Tabelle erstellen falls nicht vorhanden
            self.db.query('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )
            ''')
            
            # Admin-Benutzer anlegen
            admin_pw_hash = generate_password_hash(password)
            self.db.query('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, 'admin')
            ''', [username, admin_pw_hash])
            
            return True
            
        except Exception as e:
            print(f"Setup-Fehler: {str(e)}")
            return False
            
    def needs_setup(self):
        """Prüft ob Ersteinrichtung notwendig ist"""
        try:
            result = self.db.query(
                'SELECT COUNT(*) as count FROM users',
                one=True
            )
            return result['count'] == 0
        except:
            return True
            
    def get_tools(self):
        """Holt alle Werkzeuge"""
        return self.db.query('''
            SELECT t.*,
                   l.lent_at,
                   w.firstname || ' ' || w.lastname as lent_to,
                   CASE
                       WHEN t.status = 'defect' THEN 'defect'
                       WHEN l.id IS NOT NULL THEN 'lent'
                       ELSE 'available'
                   END as current_status
            FROM tools t
            LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
            LEFT JOIN workers w ON l.worker_barcode = w.barcode
            WHERE t.deleted = 0
            ORDER BY t.name
        ''')
        
    def get_workers(self):
        """Holt alle Mitarbeiter"""
        return self.db.query('''
            SELECT w.*,
                   COUNT(l.id) as active_lendings
            FROM workers w
            LEFT JOIN lendings l ON w.barcode = l.worker_barcode AND l.returned_at IS NULL
            WHERE w.deleted = 0
            GROUP BY w.id
            ORDER BY w.lastname, w.firstname
        ''')
        
    def get_consumables(self):
        """Holt alle Verbrauchsmaterialien"""
        return self.db.query('''
            SELECT c.*,
                   CASE
                       WHEN c.quantity <= c.min_quantity THEN 'low'
                       ELSE 'ok'
                   END as stock_status
            FROM consumables c
            WHERE c.deleted = 0
            ORDER BY c.name
        ''')
        
    def create_lending(self, tool_barcode, worker_barcode):
        """Erstellt eine neue Ausleihe"""
        try:
            # Prüfen ob das Tool bereits ausgeliehen ist
            existing = self.db.query('''
                SELECT id FROM lendings 
                WHERE tool_barcode = ? AND returned_at IS NULL
            ''', [tool_barcode], one=True)
            
            if existing:
                return False
                
            # Neue Ausleihe erstellen
            self.db.query('''
                INSERT INTO lendings (tool_barcode, worker_barcode)
                VALUES (?, ?)
            ''', [tool_barcode, worker_barcode])
            
            return True
            
        except Exception as e:
            print(f"Lending-Fehler: {str(e)}")
            return False
            
    def return_tool(self, tool_barcode):
        """Gibt ein Werkzeug zurück"""
        try:
            # Ausleihe beenden
            self.db.query('''
                UPDATE lendings 
                SET returned_at = CURRENT_TIMESTAMP
                WHERE tool_barcode = ? AND returned_at IS NULL
            ''', [tool_barcode])
            
            return True
            
        except Exception as e:
            print(f"Return-Fehler: {str(e)}")
            return False 
        
    def get_tool_categories(self):
        """Holt alle vorhandenen Werkzeugkategorien"""
        try:
            results = self.db.query('''
                SELECT DISTINCT category 
                FROM tools 
                WHERE category IS NOT NULL 
                AND category != ""
                AND deleted = 0
            ''')
            return [row['category'] for row in results]
        except Exception as e:
            print(f"Fehler beim Laden der Kategorien: {str(e)}")
            return []
            
    def create_tool(self, tool_data):
        """Erstellt ein neues Werkzeug"""
        try:
            # Prüfen ob Barcode bereits existiert
            existing = self.db.query('''
                SELECT id FROM tools 
                WHERE barcode = ? AND deleted = 0
            ''', [tool_data['barcode']], one=True)
            
            if existing:
                return False
                
            # Neues Werkzeug erstellen
            self.db.query('''
                INSERT INTO tools (
                    barcode, name, description, 
                    status, category, location
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', [
                tool_data['barcode'],
                tool_data['name'],
                tool_data['description'],
                tool_data['status'],
                tool_data['category'],
                tool_data['location']
            ])
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Erstellen des Werkzeugs: {str(e)}")
            return False
            
    def update_tool(self, tool_data):
        """Aktualisiert ein bestehendes Werkzeug"""
        try:
            # Werkzeug aktualisieren
            self.db.query('''
                UPDATE tools 
                SET name = ?,
                    description = ?,
                    status = ?,
                    category = ?,
                    location = ?,
                    modified_at = CURRENT_TIMESTAMP
                WHERE barcode = ? AND deleted = 0
            ''', [
                tool_data['name'],
                tool_data['description'],
                tool_data['status'],
                tool_data['category'],
                tool_data['location'],
                tool_data['barcode']
            ])
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Werkzeugs: {str(e)}")
            return False 
        
    def get_departments(self):
        """Holt alle vorhandenen Abteilungen"""
        try:
            results = self.db.query('''
                SELECT DISTINCT department 
                FROM workers 
                WHERE department IS NOT NULL 
                AND department != ""
                AND deleted = 0
            ''')
            return [row['department'] for row in results]
        except Exception as e:
            print(f"Fehler beim Laden der Abteilungen: {str(e)}")
            return []
            
    def create_worker(self, worker_data):
        """Erstellt einen neuen Mitarbeiter"""
        try:
            # Prüfen ob Barcode bereits existiert
            existing = self.db.query('''
                SELECT id FROM workers 
                WHERE barcode = ? AND deleted = 0
            ''', [worker_data['barcode']], one=True)
            
            if existing:
                return False
                
            # Neuen Mitarbeiter erstellen
            self.db.query('''
                INSERT INTO workers (
                    barcode, firstname, lastname, 
                    department, email
                ) VALUES (?, ?, ?, ?, ?)
            ''', [
                worker_data['barcode'],
                worker_data['firstname'],
                worker_data['lastname'],
                worker_data['department'],
                worker_data['email']
            ])
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Erstellen des Mitarbeiters: {str(e)}")
            return False
            
    def update_worker(self, worker_data):
        """Aktualisiert einen bestehenden Mitarbeiter"""
        try:
            # Mitarbeiter aktualisieren
            self.db.query('''
                UPDATE workers 
                SET firstname = ?,
                    lastname = ?,
                    department = ?,
                    email = ?,
                    modified_at = CURRENT_TIMESTAMP
                WHERE barcode = ? AND deleted = 0
            ''', [
                worker_data['firstname'],
                worker_data['lastname'],
                worker_data['department'],
                worker_data['email'],
                worker_data['barcode']
            ])
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Mitarbeiters: {str(e)}")
            return False 
        
    def get_consumable_categories(self):
        """Holt alle vorhandenen Kategorien für Verbrauchsmaterialien"""
        try:
            results = self.db.query('''
                SELECT DISTINCT category 
                FROM consumables 
                WHERE category IS NOT NULL 
                AND category != ""
                AND deleted = 0
            ''')
            return [row['category'] for row in results]
        except Exception as e:
            print(f"Fehler beim Laden der Kategorien: {str(e)}")
            return []
            
    def create_consumable(self, consumable_data):
        """Erstellt ein neues Verbrauchsmaterial"""
        try:
            # Prüfen ob Barcode bereits existiert
            existing = self.db.query('''
                SELECT id FROM consumables 
                WHERE barcode = ? AND deleted = 0
            ''', [consumable_data['barcode']], one=True)
            
            if existing:
                return False
                
            # Neues Material erstellen
            self.db.query('''
                INSERT INTO consumables (
                    barcode, name, description, 
                    quantity, min_quantity,
                    category, location
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [
                consumable_data['barcode'],
                consumable_data['name'],
                consumable_data['description'],
                consumable_data['quantity'],
                consumable_data['min_quantity'],
                consumable_data['category'],
                consumable_data['location']
            ])
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Erstellen des Materials: {str(e)}")
            return False
            
    def update_consumable(self, consumable_data):
        """Aktualisiert ein bestehendes Verbrauchsmaterial"""
        try:
            # Material aktualisieren
            self.db.query('''
                UPDATE consumables 
                SET name = ?,
                    description = ?,
                    quantity = ?,
                    min_quantity = ?,
                    category = ?,
                    location = ?,
                    modified_at = CURRENT_TIMESTAMP
                WHERE barcode = ? AND deleted = 0
            ''', [
                consumable_data['name'],
                consumable_data['description'],
                consumable_data['quantity'],
                consumable_data['min_quantity'],
                consumable_data['category'],
                consumable_data['location'],
                consumable_data['barcode']
            ])
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Materials: {str(e)}")
            return False
            
    def update_consumable_quantity(self, barcode, new_quantity):
        """Aktualisiert die Menge eines Verbrauchsmaterials"""
        try:
            # Menge aktualisieren
            self.db.query('''
                UPDATE consumables 
                SET quantity = ?,
                    modified_at = CURRENT_TIMESTAMP
                WHERE barcode = ? AND deleted = 0
            ''', [new_quantity, barcode])
            
            # Nutzung protokollieren
            self.db.query('''
                INSERT INTO consumable_usages (
                    consumable_barcode, worker_barcode, quantity
                ) VALUES (?, NULL, ?)
            ''', [barcode, new_quantity])
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Menge: {str(e)}")
            return False 
        
    def get_worker_by_barcode(self, barcode):
        """Holt einen Mitarbeiter anhand des Barcodes"""
        try:
            return self.db.query('''
                SELECT w.*,
                       COUNT(l.id) as active_lendings
                FROM workers w
                LEFT JOIN lendings l ON w.barcode = l.worker_barcode 
                    AND l.returned_at IS NULL
                WHERE w.barcode = ? AND w.deleted = 0
                GROUP BY w.id
            ''', [barcode], one=True)
            
        except Exception as e:
            print(f"Fehler beim Laden des Mitarbeiters: {str(e)}")
            return None 
        
    def get_tool_by_barcode(self, barcode):
        """Holt ein Werkzeug anhand des Barcodes"""
        try:
            return self.db.query('''
                SELECT t.*,
                       l.lent_at,
                       w.firstname || ' ' || w.lastname as lent_to,
                       CASE
                           WHEN t.status = 'defect' THEN 'defect'
                           WHEN l.id IS NOT NULL THEN 'lent'
                           ELSE 'available'
                       END as current_status
                FROM tools t
                LEFT JOIN lendings l ON t.barcode = l.tool_barcode 
                    AND l.returned_at IS NULL
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.barcode = ? AND t.deleted = 0
            ''', [barcode], one=True)
            
        except Exception as e:
            print(f"Fehler beim Laden des Werkzeugs: {str(e)}")
            return None 