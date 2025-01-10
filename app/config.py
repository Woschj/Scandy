import os
from pathlib import Path

class Config:
    # Basis-Konfiguration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    
    # Datenbank-Konfiguration
    DATABASE = os.path.join(str(Path(__file__).parent.parent), 'app', 'database', 'inventory.db')
    
    # Server-Konfiguration
    SERVER_MODE = False  # Standard: Client-Modus
    SERVER_URL = os.environ.get('SERVER_URL', '')  # URL des Sync-Servers
    SYNC_INTERVAL = 300  # Sync-Intervall in Sekunden (5 Minuten)
    CLIENT_NAME = os.environ.get('CLIENT_NAME', 'default_client')
    
    # Backup-Konfiguration
    BACKUP_DIR = os.path.join(str(Path(__file__).parent.parent), 'backups')
    BACKUP_INTERVAL = 86400  # Backup-Intervall in Sekunden (24 Stunden)
    
    # Upload-Konfiguration
    UPLOAD_FOLDER = os.path.join(str(Path(__file__).parent.parent), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    @staticmethod
    def is_pythonanywhere():
        """Prüft ob die App auf PythonAnywhere läuft"""
        return 'PYTHONANYWHERE_SITE' in os.environ

    @staticmethod
    def get_project_root():
        """Gibt den absoluten Pfad zum Projektverzeichnis zurück"""
        if 'PYTHONANYWHERE_SITE' in os.environ:
            return '/home/aklann/Scandy'
        return str(Path(__file__).parent.parent)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    
    # Entwicklungsspezifische Einstellungen
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Sicherheitseinstellungen für Produktion
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 1800  # 30 Minuten
    
    # PythonAnywhere spezifische Pfade
    DATABASE = '/home/aklann/Scandy/app/database/inventory.db'
    BACKUP_DIR = '/home/aklann/Scandy/backups'
    UPLOAD_FOLDER = '/home/aklann/Scandy/uploads'

# Konfiguration basierend auf Umgebung wählen
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig if not Config.is_pythonanywhere() else ProductionConfig
} 