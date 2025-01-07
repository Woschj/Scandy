import unittest
import os
import sys
import tempfile
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import create_app
from app.models.database import Database

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """Setup-Methode, die vor jedem Test ausgeführt wird."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test_key',
            'SERVER_NAME': 'localhost:5000'
        })
        self.client = self.app.test_client()
        
        with self.app.app_context():
            Database.init_db()
            self._create_test_data()
            
    def _create_test_data(self):
        """Erstellt Basis-Testdaten in der Datenbank."""
        with Database.get_db() as conn:
            # Alte Daten löschen
            conn.execute('DELETE FROM users')
            conn.execute('DELETE FROM tools')
            conn.execute('DELETE FROM consumables')
            conn.execute('DELETE FROM workers')
            conn.execute('DELETE FROM lendings')
            conn.execute('DELETE FROM consumable_usages')
            
            # Testbenutzer erstellen
            conn.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                ('admin', generate_password_hash('admin'), 'admin')
            )
            
            # Test-Werkzeuge erstellen
            conn.execute('''
                INSERT INTO tools (barcode, name, description, status, category, location, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('TOOL001', 'Testwerkzeug', 'Ein Testwerkzeug', 'available', 'Test', 'Testort', 
                  datetime(2025, 1, 7, 11, 12, 15).strftime('%Y-%m-%d %H:%M:%S'),
                  datetime(2025, 1, 7, 11, 12, 15).strftime('%Y-%m-%d %H:%M:%S')))
            
            # Test-Verbrauchsmaterial erstellen
            conn.execute('''
                INSERT INTO consumables (barcode, name, description, quantity, min_quantity, category, location, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('CONS001', 'Testmaterial', 'Ein Testmaterial', 100, 10, 'Test', 'Testort',
                  datetime(2025, 1, 7, 11, 12, 15).strftime('%Y-%m-%d %H:%M:%S'),
                  datetime(2025, 1, 7, 11, 12, 15).strftime('%Y-%m-%d %H:%M:%S')))
            
            # Test-Mitarbeiter erstellen
            conn.execute('''
                INSERT INTO workers (barcode, firstname, lastname, department, email, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('WORK001', 'Max', 'Mustermann', 'Testabteilung', 'max.mustermann@test.de',
                  datetime(2025, 1, 7, 11, 12, 15).strftime('%Y-%m-%d %H:%M:%S'),
                  datetime(2025, 1, 7, 11, 12, 15).strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            
    def tearDown(self):
        """Cleanup nach jedem Test."""
        os.close(self.db_fd)
        os.unlink(self.db_path)
        
    def login(self, username='admin', password='admin'):
        """Hilfsmethode für Login."""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = username
            sess['role'] = 'admin'
            sess['user_id'] = 1
        
    def logout(self):
        """Hilfsmethode für Logout."""
        with self.client.session_transaction() as sess:
            sess.clear() 