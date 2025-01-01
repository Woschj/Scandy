from flask import Flask, jsonify, render_template, redirect, url_for, g, send_from_directory, session, request, flash
from flask_session import Session  # Session-Management
from .constants import Routes
import os
from datetime import datetime, timedelta
from app.utils.filters import register_filters
import logging
from app.models.database import Database
from app.utils.error_handler import handle_errors
from app.utils.db_schema import SchemaManager
from app.utils.color_settings import get_color_settings
from flask_compress import Compress
from app.models.settings import Settings

def create_app(test_config=None):
    app = Flask(__name__)
    Compress(app)  # Aktiviert gzip Komprimierung
    
    # Stelle sicher, dass das Datenbankverzeichnis existiert
    if not os.path.exists('database'):
        os.makedirs('database')
    
    # Initialisiere die Datenbank
    db_path = Database.get_database_path()
    if not os.path.exists(db_path):
        print("Initialisiere neue Datenbank...")
        Database.init_db()
        print("Datenbank erfolgreich initialisiert!")
    
    # Initialisiere die Zugriffseinstellungen innerhalb des App-Kontexts
    with app.app_context():
        try:
            # Lösche alte Einstellungen
            Database.query('DROP TABLE IF EXISTS access_settings')
            
            # Erstelle die Tabelle neu
            Database.query('''
                CREATE TABLE access_settings (
                    route TEXT PRIMARY KEY,
                    is_public BOOLEAN DEFAULT 0,
                    description TEXT
                )
            ''')
            
            # Standard-Einstellungen für Routen
            default_settings = [
                ('tools.index', 1, 'Werkzeug-Übersicht'),
                ('tools.details', 0, 'Werkzeug-Details'),  # Details erfordern Login
                ('tools.add', 0, 'Werkzeug hinzufügen'),
                ('tools.edit', 0, 'Werkzeug bearbeiten'),
                ('tools.delete', 0, 'Werkzeug löschen'),
                ('consumables.index', 1, 'Verbrauchsmaterial-Übersicht'),
                ('consumables.details', 0, 'Verbrauchsmaterial-Details'),
                ('consumables.add', 0, 'Verbrauchsmaterial hinzufügen'),
                ('workers.index', 0, 'Mitarbeiter-Übersicht'),
                ('workers.details', 0, 'Mitarbeiter-Details'),
                ('admin.dashboard', 0, 'Admin-Dashboard'),
                ('admin.access_settings', 0, 'Zugriffseinstellungen'),
                ('admin.trash', 0, 'Papierkorb'),
                ('history.view', 0, 'Verlauf'),
                ('auth.login', 1, 'Login'),
                ('auth.logout', 1, 'Logout')
            ]
            
            # Füge die Einstellungen einzeln ein
            for route, is_public, desc in default_settings:
                Database.query('''
                    INSERT OR REPLACE INTO access_settings (route, is_public, description)
                    VALUES (?, ?, ?)
                ''', [route, is_public, desc])
            
            print("Zugriffseinstellungen erfolgreich initialisiert")
            
            # Users-Tabelle prüfen/erstellen
            Database.query('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )
            ''')
            
            # Standard Admin-Account erstellen
            from werkzeug.security import generate_password_hash
            Database.query('''
                INSERT OR IGNORE INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', ['admin', generate_password_hash('admin'), 'admin'])
            
            print("Benutzer-Tabelle initialisiert")
            
        except Exception as e:
            print(f"Fehler beim Initialisieren der Zugriffseinstellungen: {e}")
    
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.update(test_config)

    # Stellen Sie sicher, dass der Instance-Ordner existiert
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Session-Konfiguration
    app.config.update(
        SECRET_KEY='dev',  # In Produktion durch sicheren Schlüssel ersetzen
        SESSION_TYPE='filesystem',
        SESSION_PERMANENT=True,  # Session bleibt auch nach Browser-Schließung erhalten
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),  # Session-Dauer: 7 Tage
        SESSION_COOKIE_SECURE=False,  # True in Produktion
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_FILE_DIR='flask_session',  # Spezifischer Ordner für Session-Dateien
        SESSION_FILE_THRESHOLD=500  # Maximale Anzahl von Session-Dateien
    )

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

    # Blueprints registrieren
    from app.routes import auth, admin, tools, workers, consumables, api, inventory, quick_scan, history
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(workers.bp)
    app.register_blueprint(consumables.bp)  # Ohne zusätzlichen Prefix
    app.register_blueprint(api.bp)
    app.register_blueprint(quick_scan.bp)
    app.register_blueprint(history.bp)

    # Standardroute
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

    # Stelle sicher, dass die Datenbank existiert und initialisiert ist
    Database.ensure_db_exists()

    # Cache-Einstellungen
    @app.after_request
    def add_header(response):
        # Cache statische Dateien für 1 Stunde
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
        
    # Statische Dateien effizienter ausliefern
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename,
                                 max_age=timedelta(hours=1))

    # Globaler Context Processor für Admin-Status
    @app.context_processor
    def inject_admin_status():
        return {
            'is_admin': session.get('is_admin', False),
            'routes': Routes(),
            'trash_count': get_trash_count() if session.get('is_admin') else 0
        }

    # Funktion zum Abrufen der Papierkorb-Anzahl
    def get_trash_count():
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM tools WHERE deleted = 1) +
                        (SELECT COUNT(*) FROM consumables WHERE deleted = 1) +
                        (SELECT COUNT(*) FROM workers WHERE deleted = 1) as total
                """)
                return cursor.fetchone()['total']
        except Exception as e:
            print(f"Fehler beim Ermitteln der Papierkorb-Anzahl: {str(e)}")
            return 0

    # Before Request Handler für Session-Prüfung
    @app.before_request
    def check_session():
        # Diese Routen sind immer öffentlich
        public_routes = [
            'static', 
            'auth.login', 
            'auth.logout', 
            'tools.index',
            'consumables.index'
        ]
        
        if request.endpoint in public_routes:
            return None
        
        if not session.get('is_admin'):
            flash('Diese Seite erfordert eine Anmeldung.', 'warning')
            return redirect(url_for('auth.login'))

    return app