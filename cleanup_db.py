from app import create_app
from app.models.database import Database

def cleanup_database():
    print("Starte Datenbank-Bereinigung...")
    
    # Erstelle App-Kontext ohne Server zu starten
    app = create_app()
    app.config['ENV'] = 'cleanup'  # Verhindert Server-Start
    
    with app.app_context():
        # Bereinige Sync-Tabellen
        Database.cleanup_sync_tables()
        
        # Bereinige Users-Tabelle
        Database.fix_users_table()
        
        # Bereinige Consumable Usages
        Database.fix_consumable_usages()
        
        # Zeige Debug-Informationen
        Database.debug_db_contents()
        
        print("Datenbank-Bereinigung abgeschlossen.")

if __name__ == "__main__":
    cleanup_database() 