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
from app.models.init_db import init_db
from pathlib import Path
import sys

# Backup-System importieren
sys.path.append(str(Path(__file__).parent.parent))
from backup import DatabaseBackup

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

def create_app(test_config=None):
    """Erstellt und konfiguriert die Flask-Anwendung"""
    app = Flask(__name__)
    
    # Konfiguration laden
    if test_config is None:
        app.config.from_object(Config())
    else:
        app.config.update(test_config)
        
    # Verzeichnisse erstellen falls nicht vorhanden
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)
    
    # Datenbank initialisieren
    init_db(app)
    
    # Wenn auf Render, lade Demo-Daten
    if os.environ.get('RENDER') == 'true':
        demo_data_lock = os.path.join(app.instance_path, 'demo_data.lock')
        if not os.path.exists(demo_data_lock):
            # Lösche vorhandene Benutzer
            with Database.get_db() as db:
                db.execute("DELETE FROM users")
                db.commit()
                print("Vorhandene Benutzer gelöscht")
            
            # Erstelle Admin-Benutzer
            from app.models.init_db import init_users
            if init_users('admin'):
                print("Admin-Benutzer für Render erstellt (admin/admin)")
            
            # Demo-Daten laden
            from app.models.demo_data import load_demo_data
            load_demo_data()
            print("Demo-Daten wurden geladen")
            
            # Erstelle Lock-Datei
            os.makedirs(app.instance_path, exist_ok=True)
            with open(demo_data_lock, 'w') as f:
                f.write('1')
        else:
            # Versuche das letzte Backup wiederherzustellen
            backup = DatabaseBackup(app_path=Path(__file__).parent.parent)
            latest_backup = "inventory_20250110_190000.db"
            if backup.restore_backup(latest_backup):
                print(f"Backup {latest_backup} erfolgreich wiederhergestellt")
            else:
                print("Konnte Backup nicht wiederherstellen, initialisiere neue Datenbank")
                if not init_db():
                    print("Fehler bei der Datenbankinitialisierung")
                    return None