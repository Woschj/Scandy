from flask import Flask
from flask_session import Session  # Session-Management
from .constants import Routes

def create_app():
    app = Flask(__name__)
    
    # Konfiguration
    app.config['SECRET_KEY'] = 'dev'  # In Produktion durch sichere Variable ersetzen
    app.config['SESSION_TYPE'] = 'filesystem'  # Session-Typ festlegen
    
    # Session initialisieren
    Session(app)
    
    # Globale Template-Variablen
    @app.context_processor
    def inject_globals():
        return {
            'routes': Routes(),
            'colors': {
                'primary': '#5b69a7',
                'secondary': '#4c5789',
                'accent': '#3d4675'
            }
        }
    
    # Register blueprints
    from .routes import index, inventory, admin, auth, api
    app.register_blueprint(index.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    
    return app