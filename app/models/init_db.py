from werkzeug.security import generate_password_hash
from app.models.database import Database

def init_users(password=None):
    """Initialisiert die Benutzer-Tabelle"""
    if password is None:
        password = 'admin'  # Standard-Passwort
        
    with Database.get_db() as db:
        # Users-Tabelle erstellen falls nicht vorhanden
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin'
            )
        ''')
        
        # Prüfe ob Benutzer existieren
        result = db.execute("SELECT COUNT(*) FROM users").fetchone()
        if result[0] > 0:
            print("Es existieren bereits Benutzer")
            return False
            
        # Admin-Benutzer anlegen
        admin_password = generate_password_hash(password)
        print(f"Erstelle Admin-Benutzer mit Hash: {admin_password}")  # Debug
        
        db.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', admin_password, 'admin')
        )
        db.commit()
        print("Admin-Benutzer erfolgreich erstellt")
        return True

if __name__ == '__main__':
    init_users() 