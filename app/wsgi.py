import os
import sys

# Füge den App-Pfad zum Python-Pfad hinzu
path = '/home/aklann/Scandy'
if path not in sys.path:
    sys.path.append(path)

# Importiere und erstelle die Flask-App
from app import create_app
application = create_app() 