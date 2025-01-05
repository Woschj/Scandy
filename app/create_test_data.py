import sqlite3
import os
from datetime import datetime, timedelta
import random
import logging
from app.config import Config
from app.models.database import Database

logger = logging.getLogger(__name__)

def create_test_data():
    """Erstellt realistische Testdaten für die Inventarverwaltung"""
    try:
        # Stelle sicher dass die Datenbank existiert
        Database.ensure_db_exists()
        
        # Verbindung zur Datenbank herstellen
        conn = Database.get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Erstelle Testdaten...")

        # Kategorien und Standorte
        departments = {
            'Produktion': ['Montagelinie 1', 'Montagelinie 2'],
            'Wartung': ['Instandhaltung', 'Elektrik'],
            'Logistik': ['Wareneingang', 'Versand'],
            'Qualitätssicherung': ['Eingangskontrolle', 'Endkontrolle']
        }
        
        tool_categories = {
            'Handwerkzeug': ['Hammer', 'Schraubendreher', 'Zange'],
            'Elektrowerkzeug': ['Akkuschrauber', 'Kreissäge', 'Bohrmaschine'],
            'Messwerkzeug': ['Wasserwaage', 'Messschieber', 'Multimeter'],
            'Gartenwerkzeug': ['Rasenmäher', 'Heckenschere', 'Laubbläser']
        }
        
        tool_locations = {
            'Werkstatt': ['Regal A', 'Regal B', 'Werkbank'],
            'Lager': ['Zone 1', 'Zone 2'],
            'Werkzeugwagen': ['Wagen 1', 'Wagen 2']
        }
        
        consumable_categories = {
            'Schrauben': ['Holzschrauben', 'Metallschrauben', 'Senkkopfschrauben'],
            'Muttern': ['Sechskantmuttern', 'Flügelmuttern', 'Sicherungsmuttern'],
            'Dübel': ['Kunststoffdübel', 'Metalldübel', 'Hohlraumdübel'],
            'Klebeband': ['Isolierband', 'Gewebeband', 'Doppelseitiges Klebeband'],
            'Reinigungsmittel': ['Reinigungstücher', 'Bremsenreiniger', 'Entfetter']
        }
        
        consumable_locations = {
            'Hauptlager': ['Regal 1', 'Regal 2', 'Regal 3'],
            'Werkstatt': ['Schublade A', 'Schublade B'],
            'Schrank A': ['Fach 1', 'Fach 2'],
            'Schrank B': ['Fach 1', 'Fach 2']
        }

        # 1. Erstelle Werkzeuge (zunächst alle als verfügbar)
        logger.info("Erstelle Werkzeuge...")
        tools_data = [
            ('T001', 'Hammer', 'Picard 300g Schlosserhammer', 'verfügbar', 'Handwerkzeug', 'Werkstatt'),
            ('T002', 'Akkuschrauber', 'Bosch GSR 18V-60 FC Professional', 'verfügbar', 'Elektrowerkzeug', 'Werkzeugwagen'),
            ('T003', 'Wasserwaage', 'Stabila 196-2 Digital 60cm', 'verfügbar', 'Messwerkzeug', 'Werkstatt'),
            ('T004', 'Kreissäge', 'Makita DHS680Z 18V', 'verfügbar', 'Elektrowerkzeug', 'Werkstatt'),
            ('T005', 'Schraubendreher-Set', 'Wera Kraftform XXL 2', 'verfügbar', 'Handwerkzeug', 'Werkzeugwagen'),
            ('T006', 'Multimeter', 'Fluke 175 True RMS', 'verfügbar', 'Messwerkzeug', 'Werkstatt'),
            ('T007', 'Laubbläser', 'Stihl BGA 57', 'verfügbar', 'Gartenwerkzeug', 'Lager')
        ]
        
        for tool in tools_data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO tools 
                    (barcode, name, description, status, category, location, created_at, modified_at, deleted)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
                ''', tool)
            except sqlite3.IntegrityError as e:
                logger.warning(f"Konnte Werkzeug nicht erstellen: {e}")

        # 2. Erstelle Mitarbeiter mit realistischen Abteilungszuordnungen
        logger.info("Erstelle Mitarbeiter...")
        workers_data = [
            # Produktion
            ('W001', 'Max', 'Mustermann', 'Produktion', 'max.mustermann@firma.de'),
            ('W002', 'Lisa', 'Weber', 'Produktion', 'lisa.weber@firma.de'),
            # Wartung
            ('W003', 'Peter', 'Schmidt', 'Wartung', 'peter.schmidt@firma.de'),
            ('W004', 'Anna', 'Müller', 'Wartung', 'anna.mueller@firma.de'),
            # Logistik
            ('W005', 'Thomas', 'Klein', 'Logistik', 'thomas.klein@firma.de'),
            # Qualitätssicherung
            ('W006', 'Sarah', 'Wagner', 'Qualitätssicherung', 'sarah.wagner@firma.de')
        ]
        
        for worker in workers_data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO workers 
                    (barcode, firstname, lastname, department, email, created_at, modified_at, deleted)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
                ''', worker)
            except sqlite3.IntegrityError as e:
                logger.warning(f"Konnte Mitarbeiter nicht erstellen: {e}")

        # 3. Erstelle Verbrauchsmaterial mit realistischen Mengen
        logger.info("Erstelle Verbrauchsmaterial...")
        consumables_data = [
            # Schrauben mit hohem Verbrauch
            ('C001', 'Spax 4x30', 'Universalschrauben A2 200 Stk', 1000, 200, 'Schrauben', 'Hauptlager'),
            ('C002', 'Spax 5x50', 'Universalschrauben A2 100 Stk', 800, 150, 'Schrauben', 'Hauptlager'),
            # Dübel mit mittlerem Verbrauch
            ('C003', 'Fischer SX 8x40', 'Nylon-Dübel 100 Stk', 300, 50, 'Dübel', 'Schrank A'),
            # Klebeband wird von allen genutzt
            ('C004', 'Isolierband', 'Schwarz 15mm x 10m', 50, 10, 'Klebeband', 'Werkstatt'),
            # Reinigungsmittel
            ('C005', 'Mehrzwecktücher', 'Putztücher Rolle 500 Blatt', 1000, 200, 'Reinigungsmittel', 'Schrank B'),
            # Muttern
            ('C006', 'Muttern M8', 'Sechskantmuttern verzinkt 100 Stk', 400, 80, 'Muttern', 'Hauptlager'),
            ('C007', 'Muttern M6', 'Sechskantmuttern verzinkt 100 Stk', 600, 100, 'Muttern', 'Hauptlager')
        ]
        
        for consumable in consumables_data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO consumables 
                    (barcode, name, description, quantity, min_quantity, category, location, created_at, modified_at, deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
                ''', consumable)
            except sqlite3.IntegrityError as e:
                logger.warning(f"Konnte Verbrauchsmaterial nicht erstellen: {e}")

        # 4. Erstelle einige Ausleihen und aktualisiere alle relevanten Tabellen
        logger.info("Erstelle Ausleihen...")
        
        def create_lending(cursor, tool_barcode, worker_barcode, lent_at, returned_at=None):
            """Erstellt eine Ausleihe mit allen notwendigen Datenbankeinträgen"""
            try:
                # 1. Erstelle den Haupteintrag in der lendings Tabelle
                cursor.execute('''
                    INSERT INTO lendings 
                    (tool_barcode, worker_barcode, lent_at, returned_at, modified_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                ''', (
                    tool_barcode,
                    worker_barcode,
                    lent_at.strftime('%Y-%m-%d %H:%M:%S'),
                    returned_at.strftime('%Y-%m-%d %H:%M:%S') if returned_at else None
                ))
                
                # 2. Aktualisiere den Werkzeugstatus
                new_status = 'verfügbar' if returned_at else 'ausgeliehen'
                cursor.execute('''
                    UPDATE tools 
                    SET status = ?,
                        modified_at = datetime('now')
                    WHERE barcode = ?
                ''', (new_status, tool_barcode))
                
                return True
            except sqlite3.IntegrityError as e:
                logger.warning(f"Fehler beim Erstellen der Ausleihe: {e}")
                return False

        def create_consumable_usage(cursor, consumable_barcode, worker_barcode, quantity, used_at):
            """Erstellt eine Verbrauchsmaterial-Nutzung mit allen notwendigen Datenbankeinträgen"""
            try:
                # 1. Prüfe ob genügend Bestand vorhanden ist
                cursor.execute('''
                    SELECT quantity FROM consumables
                    WHERE barcode = ?
                ''', (consumable_barcode,))
                current_quantity = cursor.fetchone()[0]
                
                if current_quantity < quantity:
                    logger.warning(f"Nicht genügend Bestand für {consumable_barcode}: {current_quantity} < {quantity}")
                    return False
                
                # 2. Erstelle den Nutzungseintrag
                cursor.execute('''
                    INSERT INTO consumable_usages 
                    (consumable_barcode, worker_barcode, quantity, used_at, modified_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                ''', (
                    consumable_barcode,
                    worker_barcode,
                    quantity,
                    used_at.strftime('%Y-%m-%d %H:%M:%S')
                ))
                
                # 3. Aktualisiere den Bestand
                cursor.execute('''
                    UPDATE consumables 
                    SET quantity = quantity - ?,
                        modified_at = datetime('now')
                    WHERE barcode = ?
                ''', (quantity, consumable_barcode))
                
                # 4. Prüfe ob Mindestbestand unterschritten wurde
                cursor.execute('''
                    SELECT quantity, min_quantity FROM consumables
                    WHERE barcode = ?
                ''', (consumable_barcode,))
                new_quantity, min_quantity = cursor.fetchone()
                
                if new_quantity <= min_quantity:
                    logger.warning(f"Mindestbestand unterschritten für {consumable_barcode}: {new_quantity} <= {min_quantity}")
                    
                return True
            except sqlite3.IntegrityError as e:
                logger.warning(f"Fehler beim Erstellen der Verbrauchsmaterial-Nutzung: {e}")
                return False

        # Aktive Ausleihen erstellen
        tools_to_lend = ['T002', 'T006']  # Akkuschrauber und Multimeter
        
        for tool_barcode in tools_to_lend:
            if tool_barcode == 'T002':  # Akkuschrauber -> Produktion/Wartung
                worker_barcode = random.choice(['W001', 'W002', 'W003', 'W004'])
            else:  # Multimeter -> Wartung/Qualitätssicherung
                worker_barcode = random.choice(['W003', 'W004', 'W006'])
            
            lent_at = datetime.now() - timedelta(days=random.randint(1, 5))
            create_lending(cursor, tool_barcode, worker_barcode, lent_at)

        # Historische Ausleihen
        historical_lendings = [
            # Hammer wurde von Produktion ausgeliehen
            ('T001', 'W001', 15),
            ('T001', 'W002', 10),
            # Kreissäge wurde von Wartung ausgeliehen
            ('T004', 'W003', 20),
            # Schraubendreher von verschiedenen Abteilungen
            ('T005', 'W001', 8),
            ('T005', 'W003', 12),
            ('T005', 'W005', 5)
        ]
        
        for tool_barcode, worker_barcode, days_ago in historical_lendings:
            lent_at = datetime.now() - timedelta(days=days_ago)
            returned_at = lent_at + timedelta(hours=random.randint(2, 8))
            create_lending(cursor, tool_barcode, worker_barcode, lent_at, returned_at)

        # Setze Kreissäge auf 'in Reparatur'
        try:
            cursor.execute('''
                UPDATE tools 
                SET status = 'in Reparatur',
                    modified_at = datetime('now')
                WHERE barcode = 'T004'
            ''')
        except sqlite3.IntegrityError as e:
            logger.warning(f"Konnte Werkzeugstatus nicht auf 'in Reparatur' setzen: {e}")

        # Verbrauchsmaterial-Nutzungen
        usage_patterns = [
            # Schrauben werden häufig von Produktion/Wartung genutzt
            ('C001', ['W001', 'W002', 'W003', 'W004'], (10, 50)),  # Spax 4x30
            ('C002', ['W001', 'W002', 'W003', 'W004'], (5, 30)),   # Spax 5x50
            # Dübel werden hauptsächlich von Wartung genutzt
            ('C003', ['W003', 'W004'], (5, 20)),                    # Dübel
            # Klebeband wird von allen genutzt
            ('C004', ['W001', 'W002', 'W003', 'W004', 'W005', 'W006'], (1, 3)),
            # Reinigungstücher werden von allen genutzt
            ('C005', ['W001', 'W002', 'W003', 'W004', 'W005', 'W006'], (10, 50)),
            # Muttern werden hauptsächlich von Produktion/Wartung genutzt
            ('C006', ['W001', 'W002', 'W003', 'W004'], (5, 20)),   # M8
            ('C007', ['W001', 'W002', 'W003', 'W004'], (5, 25))    # M6
        ]
        
        for consumable_barcode, workers, quantity_range in usage_patterns:
            for _ in range(random.randint(3, 8)):
                used_at = datetime.now() - timedelta(days=random.randint(0, 30))
                worker_barcode = random.choice(workers)
                quantity = random.randint(quantity_range[0], quantity_range[1])
                create_consumable_usage(cursor, consumable_barcode, worker_barcode, quantity, used_at)

        # 6. Erstelle einen Admin-Benutzer
        logger.info("Erstelle Admin-Benutzer...")
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', ('admin', 'pbkdf2:sha256:260000$gqGRc8SXPFeOwwBk$4ac91b6a6dcf2857ea9e914b1a661728e495577e4870b3b5947c27dda5eb90c4', 'admin'))
        except sqlite3.IntegrityError as e:
            logger.warning(f"Konnte Admin-Benutzer nicht erstellen: {e}")

        # 7. Setze Grundeinstellungen
        logger.info("Setze Grundeinstellungen...")
        settings_data = [
            ('server_mode', '0', 'Client-Modus'),
            ('server_url', '', 'Keine Server-URL konfiguriert'),
            ('auto_sync', '0', 'Automatische Synchronisation deaktiviert')
        ]
        
        for setting in settings_data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value, description)
                    VALUES (?, ?, ?)
                ''', setting)
            except sqlite3.IntegrityError as e:
                logger.warning(f"Konnte Einstellung nicht setzen: {e}")

        # Commit und Verbindung schließen
        conn.commit()
        conn.close()
        
        logger.info("Testdaten erfolgreich erstellt!")
        return True
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Testdaten: {str(e)}")
        return False

if __name__ == '__main__':
    create_test_data() 