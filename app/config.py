import os
from datetime import timedelta

class Config:
    SECRET_KEY = 'dev'
    DATABASE = 'instance/scandy.db'
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'application/javascript']
    
    # Basis-Einstellungen
    DATABASE_PATH = 'database/inventory.db'
    UPLOAD_FOLDER = 'uploads'
    
    # Server/Client Einstellungen
    SERVER_MODE = True  # Erstmal immer im Server-Modus
    SERVER_HOST = '0.0.0.0'  # Erlaubt Zugriff von außen
    SERVER_PORT = 5000
    SERVER_URL = None  # Keine Sync-URL im Server-Modus
    SYNC_INTERVAL = 300  # 5 Minuten 