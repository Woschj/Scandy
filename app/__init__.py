"""
Hauptmodul der Scandy-Anwendung
------------------------------

Dieses Modul initialisiert die Flask-Anwendung und konfiguriert alle notwendigen Komponenten.

Komponenten-Struktur:
1. Blueprints (app/blueprints/):
   - tools.py: Werkzeugverwaltung
   - workers.py: Mitarbeiterverwaltung
   - consumables.py: Verbrauchsmaterialverwaltung

2. Models (app/models/):
   - tool.py: Werkzeug-Datenmodell
   - worker.py: Mitarbeiter-Datenmodell
   - consumable.py: Verbrauchsmaterial-Datenmodell
   - database.py: Datenbankverbindung
   - settings.py: Anwendungseinstellungen

3. Routes (app/routes/):
   - Alle Endpunkte der Anwendung
   - API-Endpunkte für AJAX-Aufrufe

4. Utils (app/utils/):
   - auth.py: Authentifizierung
   - error_handler.py: Fehlerbehandlung
   - logger.py: Logging-Konfiguration

Initialisierungsprozess:
1. Flask-App erstellen
2. Konfiguration laden
3. Datenbank initialisieren
4. Blueprints registrieren
5. Error Handler einrichten
6. Template-Filter registrieren

Verwendung:
- Wird von server.py oder wsgi.py importiert
- Stellt die Flask-App-Instanz bereit
"""

from flask import Flask, jsonify, render_template, redirect, url_for, g, send_from_directory, session, request, flash
from flask_session import Session  # Session-Management
from .constants import Routes
import os
from datetime import datetime, timedelta
from app.utils.filters import register_filters
import logging
from app.models.database import Database
from app.utils.error_handler import handle_errors
from app.utils.db_schema import SchemaManager
from app.utils.color_settings import get_color_settings
from flask_compress import Compress
from app.models.settings import Settings
from app.utils.auth_utils import needs_setup
from app.models.init_db import init_users as init_database_users
from pathlib import Path
import sys
from flask_login import LoginManager
from app.models.user import User

# Backup-System importieren
sys.path.append(str(Path(__file__).parent.parent))
from backup import DatabaseBackup

# Logger einrichten
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

login_manager = LoginManager()

class Config:
    @staticmethod
    def init_server():
        pass

    @staticmethod
    def init_client(server_url=None):
        pass

    @staticmethod
    def is_pythonanywhere():
        # This is a placeholder implementation. You might want to implement a more robust check for PythonAnywhere
        return False

def ensure_directories_exist():
    """Stellt sicher, dass alle benötigten Verzeichnisse existieren"""
    from app.config import config
    current_config = config['default']()
    
    # Liste der zu erstellenden Verzeichnisse
    directories = [
        os.path.dirname(current_config.DATABASE),
        current_config.BACKUP_DIR,
        current_config.UPLOAD_FOLDER
    ]
    
    # Verzeichnisse erstellen
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Verzeichnis erstellt: {directory}")
        else:
            logging.info(f"Verzeichnis existiert bereits: {directory}")

def cleanup_database():
    """Bereinigt die Datenbank von ungültigen Einträgen"""
    try:
        logger.info("Führe automatische Datenbankbereinigung durch...")
        with Database.get_db() as db:
            # Finde und lösche Ausleihungen für nicht existierende Werkzeuge
            invalid_lendings = db.execute('''
                SELECT l.*, t.barcode as tool_exists
                FROM lendings l
                LEFT JOIN tools t ON l.tool_barcode = t.barcode
                WHERE t.barcode IS NULL
                AND l.returned_at IS NULL
            ''').fetchall()
            
            if invalid_lendings:
                logger.info(f"Gefundene ungültige Ausleihungen: {len(invalid_lendings)}")
                for lending in invalid_lendings:
                    logger.info(f"Ungültige Ausleihe gefunden: {dict(lending)}")
                
                db.execute('''
                    DELETE FROM lendings
                    WHERE id IN (
                        SELECT l.id
                        FROM lendings l
                        LEFT JOIN tools t ON l.tool_barcode = t.barcode
                        WHERE t.barcode IS NULL
                        AND l.returned_at IS NULL
                    )
                ''')
                db.commit()
                logger.info(f"{len(invalid_lendings)} ungültige Ausleihungen wurden gelöscht")
    except Exception as e:
        logger.error(f"Fehler bei der automatischen Datenbankbereinigung: {str(e)}")

def create_app(test_config=None):
    """Erstellt und konfiguriert die Flask-Anwendung"""
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static')
    
    # Basis-Konfiguration
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-123'),
        SESSION_TYPE='filesystem',
        SESSION_COOKIE_SAMESITE='Lax',  # Cookie SameSite-Einstellung
        SESSION_COOKIE_SECURE=False,     # Für lokale Entwicklung auf False
        PERMANENT_SESSION_LIFETIME=timedelta(days=1)
    )
    
    # Session-Konfiguration
    Session(app)
    
    # Konfiguration laden
    if test_config is None:
        app.config.from_object(Config())
    else:
        app.config.update(test_config)
        
    # Verzeichnisse erstellen falls nicht vorhanden
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)
    
    # Blueprints registrieren
    from app.routes import (
        main, auth, admin, tools, workers, 
        consumables, lending, dashboard, history, 
        quick_scan, api, tickets
    )
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(workers.bp)
    app.register_blueprint(consumables.bp)
    app.register_blueprint(lending.bp, url_prefix='/lending')
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(history.bp)
    app.register_blueprint(quick_scan.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(tickets.bp, url_prefix='/tickets')
    
    # Fehlerbehandlung registrieren
    handle_errors(app)
    
    # Filter registrieren
    register_filters(app)
    
    # Komprimierung aktivieren
    Compress(app)
    
    # Stelle sicher, dass alle Verzeichnisse existieren
    ensure_directories_exist()
    
    # Datenbank initialisieren
    with app.app_context():
        try:
            # Stelle sicher, dass das Datenbankverzeichnis existiert
            from app.config import config
            current_config = config['default']()
            os.makedirs(os.path.dirname(current_config.DATABASE), exist_ok=True)
            
            # Initialisiere die Datenbank
            db = Database()
            db.ensure_db_exists()
            
            # Initialisiere alle Tabellen
            from app.models.database import init_db
            init_db()
            
            # Initialisiere Benutzer
            init_database_users(app)
            
            # Schema-Manager für zusätzliche Einstellungen
            schema_manager = SchemaManager(db)
            schema_manager.init_tables()  # Erstellt alle Tabellen inkl. user_permissions
            schema_manager.init_schema()
            schema_manager.init_settings()
            
            # Führe Datenbankbereinigung durch
            cleanup_database()
            
            # Berechtigungen initialisieren
            from app.models.init_db import init_permissions, init_default_roles
            init_default_roles()  # Erstellt Rollen
            init_permissions()    # Erstellt Berechtigungen und verknüpft sie mit Rollen
            
            logging.info("Datenbank erfolgreich initialisiert")
            
        except Exception as e:
            logging.error(f"Fehler bei der Datenbankinitialisierung: {str(e)}")
            raise
    
    return app