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

    @staticmethod
    def is_pythonanywhere():
        # This is a placeholder implementation. You might want to implement a more robust check for PythonAnywhere
        return False

def ensure_directories_exist():
    """Stellt sicher, dass alle benötigten Verzeichnisse existieren"""
    from app.config import config
    current_config = config['default']()
    
    # Liste der zu erstellenden Verzeichnisse
    directories = [
        os.path.dirname(current_config.DATABASE),
        current_config.BACKUP_DIR,
        current_config.UPLOAD_FOLDER
    ]
    
    # Verzeichnisse erstellen
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Verzeichnis erstellt: {directory}")
        else:
            logging.info(f"Verzeichnis existiert bereits: {directory}")

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

    # Setze die Index-Routen
    @app.route('/')
    @app.route('/index')
    def index():
        # Statistiken berechnen
        from app.models.database import Database
        db = Database.get_db()
        
        # Tool Statistiken
        tool_stats = db.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'verfügbar' THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN status = 'defekt' THEN 1 ELSE 0 END) as defect
            FROM tools
        ''').fetchone()
        
        # Consumable Statistiken
        consumable_stats = db.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE 
                    WHEN quantity > min_quantity THEN 1 
                    ELSE 0 
                END) as sufficient,
                SUM(CASE 
                    WHEN quantity <= min_quantity THEN 1 
                    ELSE 0 
                END) as warning,
                0 as critical
            FROM consumables
        ''').fetchone()
        
        # Worker Statistiken Gesamt
        worker_stats = db.execute('''
            SELECT COUNT(*) as total
            FROM workers
        ''').fetchone()
        
        # Worker Statistiken nach Abteilung
        departments = db.execute('''
            SELECT department as name, COUNT(*) as count
            FROM workers
            GROUP BY department
            ORDER BY department
        ''').fetchall()
        
        # Füge die Abteilungsstatistiken zum worker_stats Dictionary hinzu
        worker_stats = dict(worker_stats)
        worker_stats['by_department'] = departments
        
        return render_template('index.html',
                             tool_stats=tool_stats,
                             worker_stats=worker_stats,
                             consumable_stats=consumable_stats)

    # Blueprints DANACH registrieren
    from app.routes import init_app
    init_app(app)

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
        if 'text/html' in response.content_type:
            # Keine Caching für HTML-Seiten
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        else:
            # Cache statische Dateien für 1 Stunde
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
        
        # Nur ausführen, wenn nicht auf PythonAnywhere
        if not Config.is_pythonanywhere():
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

    # Backup-System initialisieren
    backup = DatabaseBackup(app_path=Path(__file__).parent.parent)
    
    # Scheduler temporär deaktiviert
    """
    # Scheduler nur starten, wenn wir nicht auf PythonAnywhere sind
    if not Config.is_pythonanywhere():
        # Scheduler für automatische Backups einrichten
        scheduler = BackgroundScheduler()
        scheduler.add_job(backup.create_backup, 'cron', hour=7, minute=0)  # 7:00 Uhr
        scheduler.add_job(backup.create_backup, 'cron', hour=19, minute=0) # 19:00 Uhr
        scheduler.start()
    """

    # Stelle sicher, dass alle Verzeichnisse existieren
    ensure_directories_exist()

    return app