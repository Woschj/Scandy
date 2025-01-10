import os
from pathlib import Path

class Config:
    # Basis-Verzeichnis der Anwendung
    BASE_DIR = Path(__file__).parent.parent
    
    # Sicherheitseinstellungen
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    SESSION_TYPE = 'filesystem'
    
    # Datenbank-Einstellungen
    DATABASE = os.path.join(BASE_DIR, 'app', 'database', 'inventory.db')
    
    # Upload-Einstellungen
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    
    # Backup-Einstellungen
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    BACKUP_INTERVAL = 24  # Stunden zwischen Backups
    
    # Debug und Logging
    DEBUG = False
    TESTING = False
    
    # Produktionseinstellungen
    PREFERRED_URL_SCHEME = 'https'  # Für SSL
    SESSION_COOKIE_SECURE = True    # Cookies nur über HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Cookies nicht via JavaScript zugreifbar
    PERMANENT_SESSION_LIFETIME = 1800  # Session-Timeout nach 30 Minuten

    @staticmethod
    def get_project_root():
        """Gibt den absoluten Pfad zum Projektverzeichnis zurück"""
        return str(Path(__file__).parent.parent)

    @classmethod
    def get_absolute_database_path(cls):
        """Gibt den absoluten Pfad zur Datenbank zurück"""
        return os.path.join(cls.get_project_root(), 'app', 'database', 'inventory.db')

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig  # Änderung auf ProductionConfig als Standard
} 