#!/bin/sh

# Wechsle in das Projektverzeichnis
cd /app

# Stelle sicher, dass die Backup-Verzeichnisse existieren
mkdir -p /app/backups
mkdir -p /app/logs

# Erstelle Backup mit Flask-Anwendungskontext
python3 -c "
from server import create_app
from backup import DatabaseBackup
import logging
import os
import shutil
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(
    filename='/app/logs/backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    # Definiere Pfade
    db_path = '/app/app/database/inventory.db'
    backup_dir = '/app/backups'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'inventory_{timestamp}.db')
    
    # Prüfe ob Datenbank existiert
    if not os.path.exists(db_path):
        raise FileNotFoundError(f'Datenbank nicht gefunden: {db_path}')
    
    logging.info(f'Starte Backup von {db_path} nach {backup_path}')
    
    # Erstelle Backup durch direkte Kopie
    shutil.copy2(db_path, backup_path)
    
    # Prüfe ob Backup erstellt wurde
    if os.path.exists(backup_path):
        backup_size = os.path.getsize(backup_path)
        logging.info(f'Backup erfolgreich erstellt ({backup_size} bytes)')
    else:
        raise Exception('Backup-Datei wurde nicht erstellt')
        
except Exception as e:
    logging.error(f'Kritischer Fehler beim Backup: {str(e)}')"

# Alte Backups aufräumen (älter als 30 Tage)
find /app/backups -name "inventory_*.db" -type f -mtime +30 -delete
find /app/backups -name "inventory_*.json" -type f -mtime +30 -delete

# Backup-Status in Log schreiben
echo "[$(date)] Backup-Prozess abgeschlossen" >> /app/logs/backup.log 