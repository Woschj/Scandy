"""
Automatisches Backup-System
------------------------

Dieses Modul implementiert ein robustes Backup-System für die Scandy-Anwendung.

Hauptfunktionen:
1. Automatische Datenbank-Backups (inventory.db und users.db)
2. Datei-Backup (Uploads, Konfigurationen)
3. Rotierendes Backup-System
4. Backup-Verifizierung

Backup-Typen:
- Vollständiges Backup: Komplette Datenbanken
- Hot-Backup: Während des Betriebs
"""

import os
import shutil
from datetime import datetime, timedelta
import glob
import logging
from pathlib import Path
import json
import sqlite3

class DatabaseBackup:
    def __init__(self, app_path=None):
        # Basis-Verzeichnisse
        self.base_dir = Path('/app')
        self.internal_backup_dir = self.base_dir / 'internal_backups'
        
        # Datenbank-Pfade
        self.inventory_db_path = self.base_dir / 'database' / 'inventory.db'
        self.users_db_path = self.base_dir / 'database' / 'users.db'
        self.max_days = 30

        # Stelle sicher dass Verzeichnisse existieren
        self.internal_backup_dir.mkdir(exist_ok=True)
        
        # Logging einrichten
        logging.basicConfig(
            filename=str(self.base_dir / 'logs' / 'backup.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def list_all_backups(self):
        """Listet alle verfügbaren Backups im Container auf"""
        backups = []
        try:
            for backup_file in sorted(self.internal_backup_dir.glob('inventory_*.db')):
                backup_info = {
                    'name': backup_file.name,
                    'size': backup_file.stat().st_size,
                    'created': datetime.fromtimestamp(backup_file.stat().st_mtime),
                    'type': 'Automatisch' if 'auto' in backup_file.name else 'Manuell'
                }
                
                # Prüfe ob zugehöriges Users-Backup existiert
                users_backup = self.internal_backup_dir / f"users_{backup_file.name.split('_', 1)[1]}"
                if users_backup.exists():
                    backup_info['users_backup'] = True
                    backup_info['users_backup_size'] = users_backup.stat().st_size
                
                # Metadaten laden falls vorhanden
                metadata_file = backup_file.with_suffix('.json')
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            backup_info.update(metadata)
                    except Exception as e:
                        self.logger.error(f"Fehler beim Laden der Metadaten für {backup_file.name}: {str(e)}")
                
                backups.append(backup_info)
            
            return sorted(backups, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            self.logger.error(f"Fehler beim Auflisten der Backups: {str(e)}")
            return []

    def create_backup(self, description=None):
        """Erstellt ein neues Backup beider Datenbanken im Container"""
        try:
            # Generiere Backup-Namen
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            inventory_backup_name = f"inventory_{timestamp}.db"
            users_backup_name = f"users_{timestamp}.db"
            
            inventory_backup_path = self.internal_backup_dir / inventory_backup_name
            users_backup_path = self.internal_backup_dir / users_backup_name
            
            # Erstelle Backups
            shutil.copy2(self.inventory_db_path, inventory_backup_path)
            if self.users_db_path.exists():
                shutil.copy2(self.users_db_path, users_backup_path)
            
            # Speichere Metadaten
            metadata = {
                'created_at': datetime.now().isoformat(),
                'description': description or 'Automatisches Backup',
                'inventory_size': os.path.getsize(inventory_backup_path),
                'users_size': os.path.getsize(users_backup_path) if self.users_db_path.exists() else 0,
                'type': 'Automatisch' if not description else 'Manuell'
            }
            
            with open(inventory_backup_path.with_suffix('.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Backup erfolgreich erstellt: {inventory_backup_name} und {users_backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Backups: {str(e)}")
            return False

    def restore_backup(self, backup_name):
        """Stellt ein Backup beider Datenbanken aus dem Container wieder her"""
        try:
            inventory_backup_path = self.internal_backup_dir / backup_name
            users_backup_path = self.internal_backup_dir / f"users_{backup_name.split('_', 1)[1]}"
            
            if not inventory_backup_path.exists():
                raise FileNotFoundError(f"Inventory Backup nicht gefunden: {backup_name}")

            # Erstelle Sicherungskopien der aktuellen Datenbanken
            inventory_current_backup = self.inventory_db_path.with_suffix('.bak')
            users_current_backup = self.users_db_path.with_suffix('.bak')
            
            shutil.copy2(self.inventory_db_path, inventory_current_backup)
            if self.users_db_path.exists():
                shutil.copy2(self.users_db_path, users_current_backup)

            try:
                # Kopiere Backups
                shutil.copy2(inventory_backup_path, self.inventory_db_path)
                if users_backup_path.exists() and self.users_db_path.exists():
                    shutil.copy2(users_backup_path, self.users_db_path)
                
                # Teste wiederhergestellte Datenbanken
                with sqlite3.connect(self.inventory_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                    if cursor.fetchone()[0] > 0:
                        self.logger.info(f"Backup {backup_name} erfolgreich wiederhergestellt")
                        return True
                    else:
                        raise Exception("Wiederhergestellte Datenbank scheint leer zu sein")

            except Exception as e:
                # Bei Fehler: Stelle Originale wieder her
                if inventory_current_backup.exists():
                    shutil.copy2(inventory_current_backup, self.inventory_db_path)
                if users_current_backup.exists():
                    shutil.copy2(users_current_backup, self.users_db_path)
                raise Exception(f"Fehler bei der Wiederherstellung: {str(e)}")

        except Exception as e:
            self.logger.error(f"Fehler beim Wiederherstellen des Backups: {str(e)}")
            return False

    def delete_backup(self, backup_name):
        """Löscht ein spezifisches Backup inkl. Users-Backup aus dem Container"""
        try:
            inventory_backup_path = self.internal_backup_dir / backup_name
            users_backup_path = self.internal_backup_dir / f"users_{backup_name.split('_', 1)[1]}"
            
            if inventory_backup_path.exists():
                inventory_backup_path.unlink()
                
                # Lösche auch Users-Backup falls vorhanden
                if users_backup_path.exists():
                    users_backup_path.unlink()
                
                # Lösche Metadaten
                metadata_path = inventory_backup_path.with_suffix('.json')
                if metadata_path.exists():
                    metadata_path.unlink()
                
                self.logger.info(f"Backup {backup_name} wurde gelöscht")
                return True
            else:
                self.logger.warning(f"Backup {backup_name} existiert nicht")
                return False
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen des Backups: {str(e)}")
            return False

    def cleanup_old_backups(self):
        """Löscht Backups im Container, die älter als max_days sind"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_days)
            deleted_count = 0
            
            for backup_file in self.internal_backup_dir.glob('inventory_*.db'):
                try:
                    file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        self.delete_backup(backup_file.name)
                        deleted_count += 1
                except Exception as e:
                    self.logger.error(f"Fehler beim Löschen von {backup_file}: {str(e)}")
            
            if deleted_count > 0:
                self.logger.info(f"{deleted_count} alte Backups wurden gelöscht")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aufräumen der Backups: {str(e)}")

if __name__ == '__main__':
    backup = DatabaseBackup()
    backup.create_backup() 