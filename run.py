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
        SESSION_COOKIE_SECURE=True,
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
        auth_bp, tools_bp, workers_bp, consumables_bp,
        api_bp, admin_bp, inventory_bp, quick_scan_bp, history_bp
    )

    logger.info("Registriere Blueprints...")
    app.register_blueprint(auth_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(workers_bp)
    app.register_blueprint(consumables_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(quick_scan_bp)
    app.register_blueprint(history_bp)
    
    # Context Processors registrieren
    register_context_processors(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Application Context erstellen
    with app.app_context():
        # Farbeinstellungen initialisieren
        logger.info("Initialisiere Farbeinstellungen...")
        db = Database()  # Database-Instanz erstellen
        schema_manager = SchemaManager(db)
        schema_manager.init_settings()
        
        # Struktur-Informationen ausgeben
        logger.info("Drucke Datenbank-Struktur...")
        print_database_structure()
        
        logger.info("Drucke App-Struktur...")
        print_app_structure()
    
    logger.info("Starte Entwicklungsserver...")
    app.run(debug=False, host='127.0.0.1', port=5000)
  