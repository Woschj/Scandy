from apscheduler.schedulers.background import BackgroundScheduler
from app.models.database import Database
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, app=None):
        self.app = app
        self.scheduler = BackgroundScheduler()
        
        if app is not None:
            self.init_app(app)
            
    def init_app(self, app):
        self.app = app
        
        # Starte Sync-Job wenn im Client-Modus
        if not Config.SERVER_MODE and Config.SERVER_URL:
            self.start_sync_scheduler()
            
    def start_sync_scheduler(self):
        """Startet periodische Synchronisation"""
        if not self.scheduler.running:
            self.scheduler.add_job(
                func=self.sync_job,
                trigger='interval',
                seconds=Config.SYNC_INTERVAL,
                id='sync_job'
            )
            self.scheduler.start()
            logger.info("Sync-Scheduler gestartet")
            
    def stop_sync_scheduler(self):
        """Stoppt die Synchronisation"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Sync-Scheduler gestoppt")
            
    def sync_job(self):
        """Führt die Synchronisation durch"""
        with self.app.app_context():
            try:
                result = Database.sync_with_server()
                if result['success']:
                    logger.info("Automatische Sync erfolgreich")
                else:
                    logger.error(f"Sync-Fehler: {result['message']}")
                    
            except Exception as e:
                logger.error(f"Sync-Job-Fehler: {str(e)}") 