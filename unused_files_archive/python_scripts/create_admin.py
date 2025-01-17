from app import create_app
from app.models.init_db import init_users
from app.models.database import Database

def create_admin_user():
    """Erstellt einen Admin-Benutzer"""
    print("Erstelle Admin-Benutzer...")
    
    app = create_app()
    with app.app_context():
        # Lösche vorhandene Benutzer
        with Database.get_db() as db:
            db.execute("DELETE FROM users")
            db.commit()
            print("Vorhandene Benutzer gelöscht")
        
        # Erstelle neuen Admin
        if init_users('admin'):
            print("Admin-Benutzer erfolgreich erstellt (admin/admin)")
        else:
            print("Fehler beim Erstellen des Admin-Benutzers")

if __name__ == '__main__':
    create_admin_user() 