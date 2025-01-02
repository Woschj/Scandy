class Config:
    # Basis-Einstellungen
    DATABASE_PATH = 'database/inventory.db'
    UPLOAD_FOLDER = 'uploads'
    
    # Server/Client Modus
    SERVER_MODE = False  # Standard: Client-Modus
    SERVER_HOST = 'localhost'
    SERVER_PORT = 5000
    SERVER_URL = None  # Wird dynamisch gesetzt
    SYNC_INTERVAL = 300  # Synchronisiere alle 5 Minuten
    
    @classmethod
    def init_server(cls, host='0.0.0.0', port=5000):
        """Server-Modus aktivieren"""
        cls.SERVER_MODE = True
        cls.SERVER_HOST = host
        cls.SERVER_PORT = port
        
    @classmethod
    def init_client(cls, server_url=None):
        """Client-Modus aktivieren"""
        cls.SERVER_MODE = False
        cls.SERVER_URL = server_url 