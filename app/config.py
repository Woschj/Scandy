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
    
    # Server-Einstellungen
    SERVER_HOST = '0.0.0.0'  # Erlaubt Zugriff von außen
    SERVER_PORT = 5000 