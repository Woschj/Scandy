from app.models.database import Database
import colorsys

def hex_to_hsl(hex_color):
    """Konvertiert HEX-Farbe zu HSL-Format für DaisyUI"""
    print(f'Konvertiere Farbe von HEX: {hex_color}')
    
    # Entferne das #-Zeichen
    hex_color = hex_color.lstrip('#')
    
    # Konvertiere zu RGB (0-1)
    rgb = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    print(f'RGB Werte: {rgb}')
    
    # Konvertiere zu HSL
    h, l, s = colorsys.rgb_to_hls(*rgb)
    
    # Formatiere als DaisyUI HSL-String
    hsl = f"{int(h*360)} {int(s*100)}% {int(l*100)}%"
    print(f'Konvertiert zu HSL: {hsl}')
    return hsl

def get_color_settings():
    """Holt die Farbeinstellungen aus der Datenbank und konvertiert sie ins HSL-Format"""
    with Database.get_db() as conn:
        settings = dict(conn.execute('''
            SELECT key, value FROM settings
            WHERE key IN ('primary_color', 'secondary_color', 'accent_color')
        ''').fetchall())
        
        # Konvertiere HEX zu HSL
        return {
            'primary': hex_to_hsl(settings.get('primary_color', '#570DF8')),     # Default Lila
            'secondary': hex_to_hsl(settings.get('secondary_color', '#F000B8')), # Default Pink
            'accent': hex_to_hsl(settings.get('accent_color', '#37CDBE'))        # Default Türkis
        }

def save_color_setting(key, value):
    """Speichert eine Farbeinstellung in der Datenbank"""
    print(f'Speichere Farbeinstellung: {key} = {value}')
    with Database.get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
    print('Farbeinstellung gespeichert')