from flask import Flask, redirect, url_for
from app.models.database import Database, init_db
from app.utils.structure_viewer import print_database_structure, print_app_structure
from app.utils.context_processors import register_context_processors
from app.utils.db_schema import SchemaManager
import logging
import os
from datetime import timedelta
from app import create_app  # Importiere die create_app Funktion

# Logging konfigurieren
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Erstelle die Flask-App
app = create_app()  # Nutze die create_app Funktion aus __init__.py

if __name__ == "__main__":
    # Logging-Handler hinzufügen
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    logger.info("Starte Anwendung...")
    
    # Datenbank initialisieren falls nicht vorhanden
    if not os.path.exists(Database.get_database_path()):
        logger.info("Initialisiere Datenbank...")
        Database.init_db()
        
        # Testdaten erstellen
        logger.info("Erstelle Testdaten...")
        from app.create_test_data import create_test_data
        create_test_data()
        
        db = Database()
        
        # Struktur-Informationen ausgeben
        logger.info("Drucke Datenbank-Struktur...")
        print_database_structure()
        
        logger.info("Drucke App-Struktur...")
        print_app_structure()
    
    logger.info("Starte Entwicklungsserver...")
    app.run(debug=False, host='127.0.0.1', port=5000)
  