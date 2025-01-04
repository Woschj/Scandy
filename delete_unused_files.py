from pathlib import Path

def delete_files():
    # Liste der zu löschenden Dateien
    files_to_delete = [
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

    print("Beginne mit dem Löschen der ungenutzten Dateien...")

    for file_path in files_to_delete:
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                print(f"✓ Gelöscht: {file_path}")
            except Exception as e:
                print(f"✗ Fehler beim Löschen von {file_path}: {str(e)}")
        else:
            print(f"! Datei nicht gefunden: {file_path}")

    print("\nLöschvorgang abgeschlossen!")
    print("Falls Sie die Dateien wiederherstellen möchten, nutzen Sie die Dateien aus dem Backup-Ordner.")

if __name__ == '__main__':
    # Sicherheitsabfrage
    print("ACHTUNG: Dieses Skript wird die aufgelisteten Dateien unwiderruflich löschen!")
    print("Ein Backup sollte bereits erstellt worden sein.")
    confirm = input("Möchten Sie fortfahren? (ja/nein): ")
    
    if confirm.lower() == 'ja':
        delete_files()
    else:
        print("Löschvorgang abgebrochen.") 