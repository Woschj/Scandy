import os
from waitress import serve
from app import create_app

# Setze Umgebungsvariablen für Produktion
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app'

# Erstelle die Anwendung
application = create_app()

if __name__ == "__main__":
    # Starte Waitress-Server
    print("Starting Waitress production server...")
    serve(application, host='0.0.0.0', port=5000, threads=4)
