import os
import platform
import sys
from app import create_app

def get_production_server():
    """Wählt den passenden WSGI-Server basierend auf dem Betriebssystem"""
    system = platform.system().lower()
    
    if system == "windows":
        try:
            from waitress import serve
            return ("waitress", serve)
        except ImportError:
            print("Waitress nicht installiert. Bitte installieren Sie es mit: pip install waitress")
            sys.exit(1)
    else:
        try:
            from gunicorn.app.base import BaseApplication
            
            class GunicornApp(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        self.cfg.set(key, value)

                def load(self):
                    return self.application
            
            return ("gunicorn", GunicornApp)
        except ImportError:
            print("Gunicorn nicht installiert. Bitte installieren Sie es mit: pip install gunicorn")
            sys.exit(1)

def run_server(host='0.0.0.0', port=5000):
    """Startet den Server im Entwicklungs- oder Produktionsmodus"""
    # Erstelle die Flask-App
    app = create_app()
    
    # Prüfe Umgebung
    is_development = os.environ.get('FLASK_ENV') == 'development'
    
    if is_development:
        print("Starte Entwicklungsserver...")
        app.run(debug=True, host=host, port=port)
    else:
        print("Starte Produktionsserver...")
        server_name, server = get_production_server()
        
        if server_name == "waitress":
            print(f"Verwende Waitress-Server auf {host}:{port}")
            server(app, host=host, port=port, threads=4)
        else:  # gunicorn
            options = {
                'bind': f'{host}:{port}',
                'workers': 4,
                'worker_class': 'sync',
                'timeout': 120
            }
            print(f"Verwende Gunicorn-Server auf {host}:{port}")
            server(app, options).run()

if __name__ == "__main__":
    # Setze Standardwerte für Host und Port
    HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    PORT = int(os.environ.get('SERVER_PORT', 5000))
    
    # Starte Server
    run_server(host=HOST, port=PORT) 