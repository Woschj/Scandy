import sys
import os

# Pfad zum Projektverzeichnis
project_home = os.path.expanduser('~/Scandy')
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import der Flask-App
from app import create_app
application = create_app()

if __name__ == '__main__':
    application.run()
