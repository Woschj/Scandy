import os
import sys
import subprocess
import venv
import logging
from pathlib import Path

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """Führt einen Befehl aus und loggt das Ergebnis"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Befehl erfolgreich: {command}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Fehler beim Ausführen von '{command}': {e.stderr}")
        return False

def create_venv():
    """Erstellt eine virtuelle Umgebung"""
    logger.info("Erstelle virtuelle Umgebung...")
    venv_path = Path("venv")
    
    if venv_path.exists():
        logger.info("Virtuelle Umgebung existiert bereits")
        return True
        
    try:
        venv.create("venv", with_pip=True)
        logger.info("Virtuelle Umgebung erfolgreich erstellt")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der virtuellen Umgebung: {e}")
        return False

def install_requirements():
    """Installiert alle benötigten Pakete"""
    logger.info("Installiere Abhängigkeiten...")
    
    # Bestimme den Python-Interpreter in der virtuellen Umgebung
    if sys.platform == "win32":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    return run_command(f"{pip_path} install -r requirements.txt")

def init_database():
    """Initialisiert die Datenbank"""
    logger.info("Initialisiere Datenbank...")
    
    # Stelle sicher, dass die Verzeichnisse existieren
    os.makedirs("instance", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    
    # Bestimme den Python-Interpreter in der virtuellen Umgebung
    if sys.platform == "win32":
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    # Führe Datenbankinitialisierung aus
    return run_command(f"{python_path} -c \"from app.models.database import Database; Database.init_db_schema()\"")

def main():
    """Hauptfunktion für das Setup"""
    logger.info("Starte Server-Setup...")
    
    # Erstelle virtuelle Umgebung
    if not create_venv():
        logger.error("Setup abgebrochen aufgrund von Fehlern bei der virtuellen Umgebung")
        return False
    
    # Installiere Abhängigkeiten
    if not install_requirements():
        logger.error("Setup abgebrochen aufgrund von Fehlern bei der Installation der Abhängigkeiten")
        return False
    
    # Initialisiere Datenbank
    if not init_database():
        logger.error("Setup abgebrochen aufgrund von Fehlern bei der Datenbankinitialisierung")
        return False
    
    logger.info("""
    Setup erfolgreich abgeschlossen!
    
    Um den Server zu starten:
    1. Aktivieren Sie die virtuelle Umgebung:
       - Windows: venv\\Scripts\\activate
       - Linux/Mac: source venv/bin/activate
    2. Starten Sie den Server:
       python run.py
    
    Der Server ist dann unter http://localhost:5000 erreichbar.
    """)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 