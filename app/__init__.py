from flask import Flask, jsonify
from flask_session import Session  # Session-Management
from .constants import Routes
from flask_login import LoginManager, login_required
import os
from datetime import datetime
from app.utils.filters import register_filters

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.update(test_config)

    # Stellen Sie sicher, dass der Instance-Ordner existiert
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Konfiguration
    app.config['SECRET_KEY'] = 'dev'  # In Produktion durch sichere Variable ersetzen
    app.config['SESSION_TYPE'] = 'filesystem'  # Session-Typ festlegen
    
    # Session initialisieren
    Session(app)
    
    # Datetime-Filter für Jinja2 Templates
    @app.template_filter('format_datetime')
    def format_datetime(value):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
        return value.strftime('%d.%m.%Y %H:%M')
    
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
    
    # Debug-Route OHNE Login-Erfordernis
    @app.route('/api/debug/routes')
    def list_routes():
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods))
            line = {
                'endpoint': rule.endpoint,
                'methods': methods,
                'path': str(rule)
            }
            output.append(line)

        return jsonify({
            'routes': output,
            'total': len(output)
        })

    # Test-Route für API-Verfügbarkeit
    @app.route('/api/test')
    def test_api():
        return jsonify({
            'status': 'ok',
            'message': 'API is working'
        })

    # Login Manager initialisieren
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Blueprints registrieren
    from app.routes import auth
    app.register_blueprint(auth.bp)

    from app.routes import admin
    admin.init_app(app)

    from app.routes import lending
    app.register_blueprint(lending.bp)

    # Andere Blueprints...

    @app.route('/')
    def index():
        return 'Scandy Tool Management'

    # CLI-Befehle nur lokal laden
    try:
        if os.environ.get('RENDER') != 'true':
            from app.cli import init_db_command
            app.cli.add_command(init_db_command)
    except ImportError:
        pass  # CLI-Modul ist optional

    return app