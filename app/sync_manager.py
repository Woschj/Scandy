from app.config import Config
from app.models.database import Database
import threading
import time
import logging

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialisiert den SyncManager mit der App"""
        self.app = app
        
        # Starte Sync-Thread nur wenn wir im Client-Modus sind und eine Server-URL haben
        if not Config.SERVER_MODE and Config.SERVER_URL and hasattr(Config, 'SYNC_INTERVAL'):
            self.start_sync_thread()

    def start_sync_thread(self):
        """Startet den Sync-Thread"""
        def sync_loop():
            while True:
                with self.app.app_context():
                    try:
                        result = Database.sync_with_server()
                        if result.get('success'):
                            logger.info("Sync erfolgreich")
                        else:
                            logger.warning(f"Sync fehlgeschlagen: {result.get('message')}")
                    except Exception as e:
                        logger.error(f"Fehler beim Sync: {str(e)}")
                time.sleep(Config.SYNC_INTERVAL)

        # Starte Thread nur wenn er noch nicht läuft
        if not hasattr(self, 'sync_thread') or not self.sync_thread.is_alive():
            self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
            self.sync_thread.start() 