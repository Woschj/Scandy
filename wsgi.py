<<<<<<< HEAD
from run import create_app

=======
import sys
import os

# Füge den Projektpfad zum Python-Pfad hinzu
project_path = '/home/YourPythonAnywhereUsername/YourProjectName'
if project_path not in sys.path:
    sys.path.append(project_path)

# Importiere und erstelle die App
from app import create_app
>>>>>>> parent of ef7d838 (0.2.4)
application = create_app()
app = application  # Für Gunicorn

if __name__ == '__main__':
    application.run()
