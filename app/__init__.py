from flask import Flask, jsonify, render_template, redirect, url_for, g
from flask_session import Session  # Session-Management
from .constants import Routes
from flask_login import LoginManager, login_required
import os
from datetime import datetime
from app.utils.filters import register_filters
import logging
from app.models.database import Database
from app.utils.error_handler import handle_errors
from app.utils.db_schema import SchemaManager
from app.utils.color_settings import get_color_settings

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
        try:
            with Database.get_db() as conn:
                # Papierkorb-Zähler
                trash_count = conn.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM tools WHERE deleted = 1) +
                        (SELECT COUNT(*) FROM consumables WHERE deleted = 1) +
                        (SELECT COUNT(*) FROM workers WHERE deleted = 1) as total
                """).fetchone()['total']

                return {
                    'routes': Routes(),
                    'trash_count': trash_count
                }
        except Exception as e:
            print(f"Fehler beim Laden der globalen Variablen: {str(e)}")
            return {
                'routes': Routes(),
                'trash_count': 0
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

    # User Loader hinzufügen
    @login_manager.user_loader
    def load_user(user_id):
        # Für das einfache Admin-Login
        if user_id == 'admin':
            return type('User', (), {
                'is_authenticated': True,
                'is_active': True,
                'is_anonymous': False,
                'get_id': lambda: 'admin'
            })
        return None

    # Blueprints registrieren
    from app.routes import auth, admin, tools, workers, consumables, api, inventory, quick_scan, history, lending, index
    
    # Zuerst die Basis-Blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(index.bp)  # Index-Blueprint für die Startseite
    
    # Dann die Feature-Blueprints
    admin.init_app(app)
    app.register_blueprint(tools.bp, url_prefix='/tools')
    app.register_blueprint(workers.bp, url_prefix='/workers')
    app.register_blueprint(consumables.bp, url_prefix='/inventory/consumables')
    
    # Zuletzt die unterstützenden Blueprints
    app.register_blueprint(api.bp)
    app.register_blueprint(quick_scan.bp)
    app.register_blueprint(history.bp)
    app.register_blueprint(lending.bp)
    app.register_blueprint(inventory.bp)

    @app.route('/')
    def index():
        return redirect(url_for('tools.index'))

    # CLI-Befehle nur lokal laden
    try:
        if os.environ.get('RENDER') != 'true':
            from app.cli import init_db_command
            app.cli.add_command(init_db_command)
    except ImportError:
        pass  # CLI-Modul ist optional

    # Globale Fehlerbehandlung
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html',
                             message="Die angeforderte Seite wurde nicht gefunden."), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html',
                             message="Ein interner Serverfehler ist aufgetreten."), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unbehandelter Fehler: {str(e)}")
        return render_template('error.html',
                             message="Ein unerwarteter Fehler ist aufgetreten.",
                             details=str(e)), 500

    # Logging konfigurieren
    if not app.debug:
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

    # Context Processor für globale Template-Variablen
    @app.context_processor
    def inject_colors():
        try:
            colors = get_color_settings()
            return {'colors': colors}
        except Exception as e:
            print(f"Fehler beim Laden der Farbeinstellungen: {str(e)}")
            return {'colors': {
                'primary': '259 94% 51%',
                'secondary': '314 100% 47%',
                'accent': '174 60% 51%'
            }}

    return app