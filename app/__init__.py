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
from app.sync_manager import SyncManager
from app.utils.auth_utils import needs_setup
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
import sys

# Backup-System importieren
sys.path.append(str(Path(__file__).parent.parent))
from backup import DatabaseBackup

class Config:
    @staticmethod
    def init_server():
        pass

    @staticmethod
    def init_client(server_url=None):
        pass

def create_app(test_config=None):
    app = Flask(__name__)
    Compress(app)  # Aktiviert gzip Komprimierung
    
    # Initialisiere die Datenbank vor dem App-Kontext
    Database.ensure_db_exists()
    
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
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),  # Sicherer Schlüssel
        SESSION_TYPE='filesystem',
        SESSION_PERMANENT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_SECURE=False,  # Auf True setzen wenn HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_FILE_DIR=os.path.join(app.instance_path, 'flask_session'),  # Besserer Pfad
        SESSION_FILE_THRESHOLD=500
    )

    # Stelle sicher, dass der Session-Ordner existiert
    os.makedirs(os.path.join(app.instance_path, 'flask_session'), exist_ok=True)

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
    from app.routes import auth, admin, tools, workers, consumables, api, quick_scan, history, main
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(workers.bp)
    app.register_blueprint(consumables.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(quick_scan.bp)
    app.register_blueprint(history.bp)
    app.register_blueprint(main.bp)

    # Setze die Index-Route als Startseite
    app.add_url_rule('/', endpoint='index', view_func=main.index)

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
            'auth.setup',  # Setup-Route hinzugefügt
            'auth.logout', 
            'tools.index',
            'consumables.index',
            'api.test'
        ]
        
        # Erlaube Zugriff auf statische Dateien und öffentliche Routen
        if request.endpoint in public_routes or request.endpoint == 'static':
            return None
        
        # Erlaube API-Zugriff
        if request.endpoint and request.endpoint.startswith('api.'):
            return None
        
        # Wenn Setup benötigt wird, erlaube nur Setup-Route
        if needs_setup():
            if request.endpoint != 'auth.setup':
                return redirect(url_for('auth.setup'))
            return None
        
        # Prüfe Login für alle anderen Routen
        if not session.get('is_admin'):
            if request.endpoint != 'auth.login':
                return redirect(url_for('auth.login', next=request.url))

    with app.app_context():
        # Initialisiere Sync-Manager
        sync_manager = SyncManager(app)
        app.extensions['sync_manager'] = sync_manager
        
        try:
            # Prüfe Server/Client Modus
            mode_setting = Database.query('''
                SELECT value FROM settings 
                WHERE key = 'server_mode'
            ''', one=True)
            
            if mode_setting:
                if bool(int(mode_setting['value'])):
                    Config.init_server()
                else:
                    server_url = Database.query('''
                        SELECT value FROM settings 
                        WHERE key = 'server_url'
                    ''', one=True)
                    Config.init_client(server_url['value'] if server_url else None)
            
            # Prüfe Auto-Sync Einstellung
            auto_sync = Database.query('''
                SELECT value FROM settings 
                WHERE key = 'auto_sync'
            ''', one=True)
            
            if auto_sync and bool(int(auto_sync['value'])):
                sync_manager.start_sync_scheduler()
                
        except Exception as e:
            app.logger.error(f"Fehler beim Wiederherstellen der Sync-Einstellungen: {str(e)}")

    # Nach den anderen context_processors
    @app.context_processor
    def inject_config():
        from app.config import Config  # Import hier, um Zirkelbezüge zu vermeiden
        return {'Config': Config}

    with app.app_context():
        # Überprüfe Datenbank beim Start
        print("\n=== CHECKING DATABASE AT STARTUP ===")
        Database.ensure_db_exists()
        
        # Überprüfe Verbrauchsmaterialien
        try:
            count = Database.query("SELECT COUNT(*) as count FROM consumables", one=True)
            print(f"Gefundene Verbrauchsmaterialien: {count['count']}")
            
            if count['count'] > 0:
                example = Database.query("SELECT * FROM consumables LIMIT 1", one=True)
                print("Beispiel-Datensatz:")
                print(dict(example))
        except Exception as e:
            print(f"Fehler beim Datenbankcheck: {e}")
    
    # Jinja Filter registrieren
    from app.utils.filters import register_filters
    register_filters(app)

    # Backup-System initialisieren
    backup = DatabaseBackup(app_path=Path(__file__).parent.parent)
    
    # Scheduler für automatische Backups einrichten
    scheduler = BackgroundScheduler()
    scheduler.add_job(backup.create_backup, 'cron', hour=7, minute=0)  # 7:00 Uhr
    scheduler.add_job(backup.create_backup, 'cron', hour=19, minute=0) # 19:00 Uhr
    scheduler.start()

    return app