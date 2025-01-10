import os
import socket

def get_local_ip():
    """Ermittelt die lokale IP-Adresse des Servers"""
    try:
        # Erstellt einen temporären Socket um die lokale IP zu ermitteln
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

class Config:
    # Basis-Konfiguration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'generate-a-secure-key-in-production'
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 Minuten
    
    # Datenbank
    DATABASE_PATH = os.path.join('app', 'database', 'inventory.db')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Server/Client Einstellungen
    SERVER_MODE = os.environ.get('SERVER_MODE', '1') == '1'  # Standard: Server-Modus
    SERVER_URL = os.environ.get('SERVER_URL', None)
    CLIENT_NAME = os.environ.get('CLIENT_NAME', socket.gethostname())
    SYNC_INTERVAL = int(os.environ.get('SYNC_INTERVAL', '300'))  # 5 Minuten
    LOCAL_IP = get_local_ip()
    
    # Sicherheitseinstellungen
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @staticmethod
    def get_project_root():
        """Gibt den absoluten Pfad zum Projektverzeichnis zurück"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @classmethod
    def get_absolute_database_path(cls):
        """Gibt den absoluten Pfad zur Datenbank zurück"""
        return os.path.join(cls.get_project_root(), cls.DATABASE_PATH)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Zusätzliche Produktionseinstellungen
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def init_app(cls, app):
        # Produktionsspezifische Initialisierung
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Logging-Handler für Produktion
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        file_handler = RotatingFileHandler(
            'logs/scandy.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Setze allgemeines Log-Level
        app.logger.setLevel(logging.INFO)
        app.logger.info('Scandy startup')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 