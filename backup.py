import os
import shutil
from datetime import datetime, timedelta
import glob
import logging
from pathlib import Path

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self, app_path=None):
        # Basis-Verzeichnis bestimmen
        if app_path:
            self.base_dir = Path(app_path)
        else:
            self.base_dir = Path.cwd()

        # Konfiguration
        self.db_path = self.base_dir / 'app' / 'database' / 'inventory.db'
        self.backup_dir = self.base_dir / 'backups'
        self.max_days = 7

        # Backup-Verzeichnis erstellen
        self.backup_dir.mkdir(exist_ok=True)
        logger.info(f"DatabaseBackup initialisiert mit:")
        logger.info(f"- Basis-Verzeichnis: {self.base_dir}")
        logger.info(f"- Datenbank-Pfad: {self.db_path}")
        logger.info(f"- Backup-Verzeichnis: {self.backup_dir}")
        
    def create_backup(self):
        """Erstellt ein Backup der Datenbank"""
        try:
            if not self.db_path.exists():
                logger.error(f"Datenbank nicht gefunden unter: {self.db_path}")
                return False

            # Aktuelles Datum und Uhrzeit für den Backup-Namen
            now = datetime.now()
            backup_name = f"inventory_{now.strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = self.backup_dir / backup_name

            logger.info(f"Erstelle Backup von {self.db_path} nach {backup_path}")

            # Backup erstellen
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup erfolgreich erstellt: {backup_name}")

            # Alte Backups aufräumen
            self.cleanup_old_backups()
            return True

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Backups: {str(e)}")
            return False

    def cleanup_old_backups(self):
        """Löscht Backups, die älter als max_days sind"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_days)
            
            for backup_file in self.backup_dir.glob('inventory_*.db'):
                try:
                    # Datum aus dem Dateinamen extrahieren
                    date_str = backup_file.stem.split('_')[1]
                    file_date = datetime.strptime(date_str, '%Y%m%d')
                    
                    # Backup löschen, wenn es älter als max_days ist
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        logger.info(f"Altes Backup gelöscht: {backup_file.name}")
                
                except Exception as e:
                    logger.error(f"Fehler beim Löschen des Backups {backup_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Fehler beim Aufräumen der Backups: {str(e)}")

    def list_backups(self):
        """Listet alle verfügbaren Backups auf"""
        try:
            backups = []
            logger.info(f"Suche Backups in: {self.backup_dir}")
            for backup_file in sorted(self.backup_dir.glob('inventory_*.db')):
                backup_info = {
                    'name': backup_file.name,
                    'size': backup_file.stat().st_size,
                    'created': datetime.fromtimestamp(backup_file.stat().st_mtime)
                }
                backups.append(backup_info)
            logger.info(f"Gefundene Backups: {len(backups)}")
            return backups
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Backups: {str(e)}")
            return []

if __name__ == '__main__':
    backup = DatabaseBackup()
    backup.create_backup() 