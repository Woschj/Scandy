from tests.base import BaseTestCase
from app.models.database import Database
import json
from flask import session

class ConsumablesTestCase(BaseTestCase):
    def setUp(self):
        """Setup für jeden Test."""
        super().setUp()
        # Login durchführen
        self.client.post('/auth/login', data=dict(
            username='admin',
            password='admin'
        ), follow_redirects=True)

    def test_consumable_creation(self):
        """Test für das Erstellen eines neuen Verbrauchsmaterials."""
        response = self.client.post('/consumables/add', data=dict(
            barcode='CONS002',
            name='Testmaterial 2',
            description='Ein weiteres Testmaterial',
            quantity=50,
            min_quantity=10,
            category='Test',
            location='Testort'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Überprüfen ob das Material erstellt wurde
        with self.app.app_context():
            with Database.get_db() as conn:
                material = conn.execute(
                    'SELECT * FROM consumables WHERE barcode = ?',
                    ('CONS002',)
                ).fetchone()
                self.assertIsNotNone(material)
                self.assertEqual(material['name'], 'Testmaterial 2')
                self.assertEqual(material['quantity'], 50)

    def test_consumable_usage(self):
        """Test für die Verwendung von Verbrauchsmaterial."""
        # Verbrauch vom vorhandenen Testmaterial registrieren
        response = self.client.post('/consumables/use', data=dict(
            consumable_barcode='CONS001',
            worker_barcode='WORK001',
            quantity=10
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Überprüfen ob der Bestand aktualisiert wurde
        with self.app.app_context():
            with Database.get_db() as conn:
                material = conn.execute(
                    'SELECT quantity FROM consumables WHERE barcode = ?',
                    ('CONS001',)
                ).fetchone()
                self.assertEqual(material['quantity'], 90)  # 100 - 10

                # Überprüfen ob der Verbrauch protokolliert wurde
                usage = conn.execute(
                    'SELECT * FROM consumable_usages WHERE consumable_barcode = ? ORDER BY id DESC',
                    ('CONS001',)
                ).fetchone()
                self.assertIsNotNone(usage)
                self.assertEqual(usage['quantity'], 10)

    def test_consumable_overview(self):
        """Test für die Verbrauchsmaterialübersicht."""
        response = self.client.get('/consumables', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Testmaterial', response.data)  # Prüft ob das Testmaterial angezeigt wird

    def test_low_stock_warning(self):
        """Test für die Warnung bei niedrigem Bestand."""
        # Material mit niedrigem Bestand erstellen
        self.client.post('/consumables/add', data=dict(
            barcode='CONS003',
            name='Niedriger Bestand',
            description='Fast leer',
            quantity=5,
            min_quantity=10,
            category='Test',
            location='Testort'
        ), follow_redirects=True)

        response = self.client.get('/consumables', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Niedriger Bestand', response.data)
        # Prüfen ob Warnhinweis angezeigt wird
        self.assertIn(b'warning', response.data.lower())
        
if __name__ == '__main__':
    import unittest
    unittest.main() 