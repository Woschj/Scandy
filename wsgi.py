from run import create_app
from app.models.database import Database
from app.create_test_data import create_test_data
import os

application = create_app()
app = application  # Für Gunicorn

# Datenbank initialisieren
with app.app_context():
    Database.init_db()
    if os.environ.get('RENDER') == 'true':
        try:
            create_test_data()  # Optional: Testdaten erstellen
        except:
            pass  # Ignoriere Fehler bei Testdaten

if __name__ == '__main__':
    application.run()
