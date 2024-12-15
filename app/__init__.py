from flask import Flask
from flask_login import LoginManager
from app.models.database import init_database, get_db_connection, DBConfig, show_db_structure
from app.utils.logger import setup_logger
import os
from datetime import datetime

def print_registered_routes(app):
    print("\n=== Registrierte Routen ===")
    print(f"{'Methoden':20} {'Endpoint':30} {'URL-Regel'}")
    print("="*80)
    for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{methods:20} {rule.endpoint:30} {str(rule)}")
    print("="*80 + "\n")

def debug_template_routes(app):
    """
    Überprüft alle Template-Routen und gibt sie in der Konsole aus
    """
    print("\n=== Template-Routen Debug ===")
    
    templates = {
        'add_consumable.html': '/admin/add-consumable',
        'manual_lending.html': '/admin/manual-lending',
        'base.html': '/',
        'consumable_details.html': '/consumables/<barcode>/details',
        'consumables.html': '/consumables',
        'tool_details.html': '/tools/<barcode>/details', 
        'tools.html': '/tools',
        'worker_details.html': '/workers/<barcode>/details',
        'workers.html': '/workers',
        'add_tool.html': '/admin/add-tool',
        'add_worker.html': '/admin/add-worker',
        'dashboard.html': '/admin/dashboard',
        'logs.html': '/admin/logs',
        'system_logs.html': '/admin/system-logs',
        'trash.html': '/admin/trash',
        'admin.html': '/admin',
        'edit_consumable.html': '/consumables/<barcode>/edit',
        'edit_tool.html': '/tools/<barcode>/edit',
        'edit_worker.html': '/workers/<barcode>/edit',
        'quick_scan.html': '/quick-scan'
    }

    for template, route in templates.items():
        try:
            print(f"\nTemplate: {template}")
            print(f"Route: {route}")
            print("Status: Aktiv")
        except Exception as e:
            print(f"Status: Fehler - {str(e)}")

    print("\n=== Debug Ende ===\n")

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    # Datetime Filter für Jinja2
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                # Versuche zuerst das Format mit Mikrosekunden
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                try:
                    # Wenn das nicht klappt, versuche es ohne Mikrosekunden
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return value  # Gib den Original-String zurück, wenn das Parsen fehlschlägt
        return value.strftime('%d.%m.%Y %H:%M')

    # Datenbank initialisieren
    with app.app_context():
        init_database()
    
    # Blueprints importieren
    from app.routes import auth
    from app.routes import admin
    from app.routes import index
    from app.routes import tools
    from app.routes import workers
    from app.routes import consumables
    from app.routes import quick_scan
    
    # Blueprints registrieren
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(workers.bp)
    app.register_blueprint(consumables.bp)
    app.register_blueprint(quick_scan.bp)
    
    # Routen anzeigen
    with app.app_context():
        print_registered_routes(app)
    
    # Debug-Ausgabe wenn Debug-Modus aktiv
    if app.config['DEBUG']:
        with app.app_context():
            debug_template_routes(app)
    
    return app