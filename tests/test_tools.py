from tests.base import BaseTestCase
from app.models.database import Database
import json
from datetime import datetime
from flask import session

class ToolsTestCase(BaseTestCase):
    def setUp(self):
        """Setup für jeden Test."""
        super().setUp()
        # Login durchführen
        self.client.post('/auth/login', data=dict(
            username='admin',
            password='admin'
        ), follow_redirects=True)

    def test_tool_creation(self):
        """Test für das Erstellen eines neuen Werkzeugs."""
        response = self.client.post('/tools/add', data=dict(
            barcode='TOOL002',
            name='Testwerkzeug 2',
            description='Ein weiteres Testwerkzeug',
            category='Test',
            location='Testort'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Überprüfen ob das Werkzeug erstellt wurde
        with self.app.app_context():
            with Database.get_db() as conn:
                tool = conn.execute(
                    'SELECT * FROM tools WHERE barcode = ?',
                    ('TOOL002',)
                ).fetchone()
                self.assertIsNotNone(tool)
                self.assertEqual(tool['name'], 'Testwerkzeug 2')
                self.assertEqual(tool['status'], 'Verfügbar')
        
    def test_tool_lending(self):
        """Test für das Ausleihen eines Werkzeugs."""
        # Ausleihen des vorhandenen Testwerkzeugs
        response = self.client.post('/api/lending/process', 
            json={
                'tool_barcode': 'TOOL001',
                'worker_barcode': 'WORK001'
            },
            follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Überprüfen ob das Werkzeug als ausgeliehen markiert wurde
        with self.app.app_context():
            with Database.get_db() as conn:
                tool = conn.execute(
                    'SELECT status FROM tools WHERE barcode = ?',
                    ('TOOL001',)
                ).fetchone()
                self.assertEqual(tool['status'], 'lent')
                
                # Überprüfen ob ein Ausleihvorgang registriert wurde
                lending = conn.execute(
                    'SELECT * FROM lendings WHERE tool_barcode = ?',
                    ('TOOL001',)
                ).fetchone()
                self.assertIsNotNone(lending)
                self.assertIsNone(lending['returned_at'])
        
    def test_tool_overview(self):
        """Test für die Werkzeugübersicht."""
        response = self.client.get('/tools', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Testwerkzeug', response.data)  # Prüft ob das Testwerkzeug angezeigt wird
        
    def test_tool_return(self):
        """Test für die Rückgabe eines Werkzeugs."""
        # Erst ausleihen
        self.client.post('/api/lending/process',
            json={
                'tool_barcode': 'TOOL001',
                'worker_barcode': 'WORK001'
            },
            follow_redirects=True)
        
        # Dann zurückgeben
        response = self.client.post('/api/lending/return',
            json={
                'tool_barcode': 'TOOL001'
            },
            follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Überprüfen ob das Werkzeug als verfügbar markiert wurde
        with self.app.app_context():
            with Database.get_db() as conn:
                tool = conn.execute(
                    'SELECT status FROM tools WHERE barcode = ?',
                    ('TOOL001',)
                ).fetchone()
                self.assertEqual(tool['status'], 'available')
                
                # Überprüfen ob der Ausleihvorgang als zurückgegeben markiert wurde
                lending = conn.execute(
                    'SELECT * FROM lendings WHERE tool_barcode = ? ORDER BY id DESC',
                    ('TOOL001',)
                ).fetchone()
                self.assertIsNotNone(lending)
                self.assertIsNotNone(lending['returned_at'])
        
if __name__ == '__main__':
    import unittest
    unittest.main() 