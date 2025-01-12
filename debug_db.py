from app import create_app
from app.models.database import Database

app = create_app()
with app.app_context():
    Database.debug_db_contents()
    exit(0)  # Beende das Script nach der Debug-Ausgabe 