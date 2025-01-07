import os
from datetime import timedelta

class Config:
    SECRET_KEY = 'dev'
    DATABASE = os.path.join('app', 'database', 'inventory.db')
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'application/javascript']
    
    # Basis-Einstellungen
    DATABASE_PATH = 'app/database/inventory.db'
    UPLOAD_FOLDER = 'uploads'
    
    # Server/Client Einstellungen
    SERVER_MODE = True  # Erstmal immer im Server-Modus
    SERVER_HOST = '0.0.0.0'  # Erlaubt Zugriff von außen
    SERVER_PORT = 5000
    SERVER_URL = None  # Keine Sync-URL im Server-Modus
    SYNC_INTERVAL = 300  # 5 Minuten 

    @staticmethod
    def get_project_root():
        """Gibt den absoluten Pfad zum Projektverzeichnis zurück"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @classmethod
    def get_absolute_database_path(cls):
        """Gibt den absoluten Pfad zur Datenbank zurück"""
        return os.path.abspath(cls.DATABASE_PATH) 