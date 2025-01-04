import os
import logging
from app.models.database import Database, init_db

def list_app_files():
    """Listet alle für die App relevanten Dateien auf"""
    app_files = []
    
    # Durchsuche das app-Verzeichnis rekursiv
    for root, dirs, files in os.walk('app'):
        # Ignoriere __pycache__ Verzeichnisse
        if '__pycache__' in root:
            continue
            
        for file in files:
            # Nur Python, SQL, HTML und JavaScript Dateien
            if file.endswith(('.py', '.sql', '.html', '.js')):
                full_path = os.path.join(root, file)
                app_files.append(full_path)
    
    logging.info("\n=== APP DATEIEN ===")
    for file in sorted(app_files):
        logging.info(f"📄 {file}")
    logging.info("=================\n")

if __name__ == '__main__':
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # App-Dateien auflisten
    list_app_files()
    
    logging.info("Starte Entwicklungsserver...")
    
    # Server starten
    from app import create_app
    app = create_app()
    app.run(debug=True) 