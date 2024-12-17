from flask import Flask, redirect, url_for
from app.models.database import Database
from app.utils.structure_viewer import print_database_structure, print_app_structure
from app.utils.context_processors import register_context_processors
from app.utils.db_schema import SchemaManager
import logging
import os
from datetime import timedelta

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
    app.config.update(
        SECRET_KEY='your-secret-key-here',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_NAME='scandy_session'
    )
    
    # Root Route hinzufügen
    @app.route('/')
    def index():
        return redirect(url_for('tools.index'))
    
    # Blueprints importieren und registrieren
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
    
    # Context Processors registrieren
    register_context_processors(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Application Context erstellen
    with app.app_context():
        # Farbeinstellungen initialisieren
        logger.info("Initialisiere Farbeinstellungen...")
        SchemaManager.init_settings()
        
        # Struktur-Informationen ausgeben
        logger.info("Drucke Datenbank-Struktur...")
        print_database_structure()
        
        logger.info("Drucke App-Struktur...")
        print_app_structure()
    
    logger.info("Starte Entwicklungsserver...")
    app.run(debug=True, host='0.0.0.0', port=5000)
  