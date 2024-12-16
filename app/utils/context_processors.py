from app.models.database import Database
from .color_extractor import extract_dominant_color
from app.utils.url_config import get_urls

def inject_colors():
    with Database.get_db() as conn:
        # Erst versuchen, die Farben aus den Einstellungen zu laden
        colors_query = conn.execute('''
            SELECT key, value FROM settings 
            WHERE key IN ('primary_color', 'secondary_color', 'accent_color')
        ''').fetchall()
        
        if colors_query:
            colors = {}
            for key, value in colors_query:
                color_key = key.replace('_color', '')
                colors[color_key] = value
        else:
            # Wenn keine Farben in der DB, dann Standardfarben verwenden
            colors = extract_dominant_color()
        
        return dict(colors=colors) 

def inject_settings():
    try:
        with Database.get_db() as conn:
            settings = {}
            for row in conn.execute('SELECT key, value FROM settings').fetchall():
                settings[row['key']] = row['value']
            return {'settings': settings}
    except Exception:
        return {'settings': {}}

def inject_urls():
    return {'urls': get_urls()}