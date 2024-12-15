from flask import Flask
from app.models.database import init_database
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dein-geheimer-schluessel'

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)

# Blueprints registrieren
from app.routes import auth, tools, workers, consumables, api
app.register_blueprint(auth.bp)
app.register_blueprint(tools.bp)
app.register_blueprint(workers.bp)
app.register_blueprint(consumables.bp)
app.register_blueprint(api.bp)

if __name__ == '__main__':
    if init_database():
        logging.info("Datenbank erfolgreich initialisiert")
        app.run(host='0.0.0.0', port=5000)
    else:
        logging.error("Fehler bei der Datenbankinitialisierung") 