from werkzeug.security import generate_password_hash
from app.models.database import Database

def init_users(password=None):
    """Initialisiert die Benutzer-Tabelle und erstellt einen Admin-Account"""
    print("Initialisiere Benutzer-Tabelle...")
    
    # Alte Tabelle löschen falls vorhanden
    Database.query('DROP TABLE IF EXISTS users')
    
    # Users-Tabelle neu erstellen
    Database.query('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    
    # Wenn kein Passwort übergeben wurde, nur Tabelle erstellen
    if not password:
        print("Keine Benutzer angelegt (kein Passwort)")
        return False
        
    try:
        # Admin-Benutzer anlegen
        admin_pw_hash = generate_password_hash(password)
        Database.query('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, 'admin')
        ''', ['admin', admin_pw_hash])
        print("Admin-Benutzer erfolgreich erstellt")
        return True
        
    except Exception as e:
        print(f"Fehler beim Anlegen des Admin-Benutzers: {str(e)}")
        return False

if __name__ == '__main__':
    init_users() 