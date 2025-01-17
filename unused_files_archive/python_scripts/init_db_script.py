from flask import Flask
from app.models.database import Database
from app.models.init_db import init_users
import os

def create_minimal_app():
    app = Flask(__name__)
    # Stelle sicher, dass der Datenbankpfad korrekt ist
    app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'app', 'database', 'inventory.db')
    return app

def main():
    print("Initialisiere Datenbank...")
    try:
        app = create_minimal_app()
        with app.app_context():
            # Stelle sicher, dass das Datenbankverzeichnis existiert
            os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
            
            # Initialisiere die Benutzer
            init_users(app)
            print("Datenbank wurde erfolgreich initialisiert")
            print("\nFolgende Benutzer wurden erstellt:")
            print("1. Admin (BTZ-Scandy25) - Volle Rechte")
            print("2. TechnikMA (BTZ-Admin) - Volle Rechte")
            print("3. TechnikTN (BTZ-Technik) - Eingeschränkte Rechte")
            
    except Exception as e:
        print(f"Fehler bei der Initialisierung: {str(e)}")

if __name__ == '__main__':
    main() 