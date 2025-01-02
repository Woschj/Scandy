import os
import sys

# Füge den Hauptpfad zum Python-Path hinzu
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)

from app import create_app
from app.config import Config
from werkzeug.security import generate_password_hash

def main():
    if len(sys.argv) < 2:
        print("Bitte Server-Passwort als Parameter angeben")
        print("Verwendung: python server.py <passwort>")
        sys.exit(1)
    
    # Aktiviere Server-Modus
    Config.SERVER_MODE = True
    Config.ADMIN_PASSWORD = generate_password_hash(sys.argv[1])
    
    # Erstelle und starte die App
    app = create_app()
    
    print(f"Server wird gestartet...")
    print(f"Datenbank: {Config.DATABASE_PATH}")
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main() 