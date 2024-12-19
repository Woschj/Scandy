import sys
import os

# Füge den Projektpfad zum Python-Pfad hinzu
project_path = '/home/YourPythonAnywhereUsername/YourProjectName'
if project_path not in sys.path:
    sys.path.append(project_path)

# Importiere und erstelle die App
from run import create_app
application = create_app()

if __name__ == '__main__':
    application.run()
