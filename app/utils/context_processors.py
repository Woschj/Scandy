from flask import current_app
from app.models.database import Database
from app.utils.routes import Routes

def get_colors():
    """Holt die Farbeinstellungen aus der Datenbank"""
    try:
        db = Database.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT key, value FROM settings WHERE key LIKE "color_%"')
        colors = {}
        for row in cursor.fetchall():
            key = row['key'].replace('color_', '')
            colors[key] = row['value']
        return colors
    except Exception as e:
        current_app.logger.error(f"Fehler beim Laden der Farben: {str(e)}")
        return {
            'primary': '#2c3e50',
            'secondary': '#4c5789',
            'accent': '#e74c3c',
            'background': '#ffffff',
            'text': '#2c3e50'
        }

def inject_colors():
    """Fügt die Farbvariablen in den Template-Kontext ein"""
    return {'colors': get_colors()}

def inject_routes():
    """Fügt die Routen-Konstanten in den Template-Kontext ein"""
    return {'routes': Routes}

def register_context_processors(app):
    """Registriert alle Context Processors"""
    app.context_processor(inject_colors)
    app.context_processor(inject_routes)