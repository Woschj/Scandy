import os
from pathlib import Path
import sys
from datetime import timedelta

# Basis-Verzeichnis
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Basis-Konfiguration"""
    
    # Plattformunabhängige Pfade
    DATABASE_DIR = BASE_DIR / 'app' / 'database'
    DATABASE = str(DATABASE_DIR / 'inventory.db')
    USERS_DATABASE = str(DATABASE_DIR / 'users.db')
    BACKUP_DIR = str(BASE_DIR / 'backups')
    UPLOAD_FOLDER = str(BASE_DIR / 'uploads')
    
    # Stelle sicher dass die Verzeichnisse existieren
    os.makedirs(DATABASE_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Basis-Konfiguration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-123')
    
    # Server-Konfiguration
    SERVER_MODE = False  # Standard: Client-Modus
    SERVER_URL = os.environ.get('SERVER_URL', '')  # URL des Sync-Servers
    SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')  # Server-Host
    SERVER_PORT = os.environ.get('SERVER_PORT', '5000')  # Server-Port
    SYNC_INTERVAL = 300  # Sync-Intervall in Sekunden (5 Minuten)
    CLIENT_NAME = os.environ.get('CLIENT_NAME', 'default_client')
    
    # Backup-Konfiguration
    BACKUP_INTERVAL = 86400  # Backup-Intervall in Sekunden (24 Stunden)
    
    # Upload-Konfiguration
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session-Konfiguration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = str(BASE_DIR / 'flask_session')
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    @staticmethod
    def is_pythonanywhere():
        """Überprüft, ob die Anwendung auf PythonAnywhere läuft"""
        return False

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