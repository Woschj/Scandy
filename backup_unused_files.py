import os
import shutil
from pathlib import Path
from datetime import datetime

def backup_files():
    # Liste der zu sichernden Dateien
    files_to_backup = [
        'app/blueprints/workers.py',
        'app/config.py',
        'app/constants.py',
        'app/electron/main.js',
        'app/electron/splash.html',
        'app/quickscan.py',
        'app/templates/auth/logout.html',
        'app/templates/auth/setup.html',
        'app/templates/components/quickscan_modal.html',
        'app/templates/components/quickscan_step_confirm.html',
        'app/templates/components/quickscan_step_final.html',
        'app/templates/components/quickscan_step_item.html',
        'app/templates/components/quickscan_step_worker.html',
        'app/templates/inventory/tools.html',
        'app/utils/db_schema.py',
        'app/utils/routes.py',
        'app/utils/url_config.py',
        'electron/main.js',
        'gunicorn.conf.py',
        'inventar/inventar/templates/admin/trash.html'
    ]

    # Erstelle Backup-Ordner mit Zeitstempel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f'backup_unused_files_{timestamp}')
    backup_dir.mkdir(exist_ok=True)

    print(f"Erstelle Backup in: {backup_dir}")

    # Kopiere jede Datei in den Backup-Ordner
    for file_path in files_to_backup:
        src_path = Path(file_path)
        if src_path.exists():
            # Erstelle Zielverzeichnisstruktur
            dest_path = backup_dir / file_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Kopiere Datei
                shutil.copy2(src_path, dest_path)
                print(f"✓ Backup erstellt: {file_path}")
            except Exception as e:
                print(f"✗ Fehler beim Backup von {file_path}: {str(e)}")
        else:
            print(f"! Datei nicht gefunden: {file_path}")

    print("\nBackup abgeschlossen!")
    print(f"Die Dateien wurden in '{backup_dir}' gesichert.")
    print("\nSie können die Originaldateien jetzt löschen, wenn Sie möchten.")
    print("Um die Dateien wiederherzustellen, kopieren Sie sie einfach aus dem Backup-Ordner zurück.")

if __name__ == '__main__':
    backup_files() 