from app import create_app
from app.models.database import Database
import os

def cleanup_database():
    """Bereinigt die Datenbank"""
    print("Starte Datenbank-Bereinigung...")
    
    # Lösche die Datenbank-Datei
    db_path = 'app/database/inventory.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Datenbank {db_path} gelöscht")
    
    app = create_app()
    with app.app_context():
        # Datenbank wird automatisch neu erstellt
        print("Datenbank wird neu initialisiert...")
        Database.debug_db_contents()
    
    print("Datenbank-Bereinigung abgeschlossen.")

if __name__ == '__main__':
    cleanup_database() 