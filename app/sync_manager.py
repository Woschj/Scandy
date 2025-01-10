from app.config import Config
from app.models.database import Database
import threading
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import os

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, app):
        self.app = app
        self.sync_interval = app.config.get('SYNC_INTERVAL', 300)  # Standard: 5 Minuten
        self.scheduler = None
        self.sync_thread = None
        self.stop_flag = False

    def start_sync_scheduler(self):
        """Startet den Scheduler für automatische Synchronisation"""
        # Nicht auf PythonAnywhere ausführen
        if 'PYTHONANYWHERE_SITE' in os.environ or os.path.exists('/var/www'):
            self.app.logger.info("Sync-Scheduler auf PythonAnywhere deaktiviert")
            return

        if not self.scheduler:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(
                self.sync_all, 
                'interval', 
                seconds=self.sync_interval,
                id='sync_job'
            )
            self.scheduler.start()
            self.app.logger.info(f"Sync-Scheduler gestartet (Intervall: {self.sync_interval} Sekunden)") 