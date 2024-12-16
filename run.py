from flask import Flask
from app.models.database import Database
from app.utils.structure_viewer import print_database_structure, print_app_structure
from app.utils.context_processors import register_context_processors
import logging
import os

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    # Flask-App erstellen
    app = Flask(__name__, 
        template_folder='app/templates',
        static_folder='app/static'
    )
    
    # Secret Key setzen
    app.config['SECRET_KEY'] = 'dev'
    
    # Context Processors registrieren
    register_context_processors(app)
    
    with app.app_context():
        logger.info("Initialisiere Anwendung...")
        
        # Stelle sicher, dass der Datenbankordner existiert
        if not os.path.exists('database'):
            logger.info("Erstelle Datenbankverzeichnis...")
            os.makedirs('database')
            
        # Initialisiere die Datenbank
        Database.init_db()
        logger.info("Datenbank initialisiert")
        
        # Zeige Datenbankstruktur
        logger.info("Datenbankstruktur:")
        print_database_structure()
        
        # Zeige Anwendungsstruktur
        logger.info("Anwendungsstruktur:")
        print_app_structure()

    # Importiere die Blueprints und registriere sie
    from app.routes import (
        auth, tools, workers, consumables, api, 
        admin, inventory, quick_scan, history
    )

    logger.info("Registriere Blueprints...")
    app.register_blueprint(auth.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(workers.bp)
    app.register_blueprint(consumables.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(inventory.bp, url_prefix='/inventory')
    app.register_blueprint(quick_scan.bp)
    app.register_blueprint(history.bp)

    # Debug-Ausgabe der registrierten Routen
    logger.info("Registrierte Routen:")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
        
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starte Entwicklungsserver...")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)  # use_reloader=False deaktiviert den Reloader
  