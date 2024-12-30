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
    """Holt die Farbeinstellungen aus der Datenbank"""
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key, value FROM settings 
                WHERE key IN ('primary_color', 'secondary_color', 'accent_color')
            """)
            settings = {row['key'].replace('_color', ''): row['value'] 
                       for row in cursor.fetchall()}
            
            # Fallback-Werte falls keine Einstellungen gefunden
            return {
                'primary': settings.get('primary', '259 94% 51%'),
                'secondary': settings.get('secondary', '314 100% 47%'),
                'accent': settings.get('accent', '174 60% 51%')
            }
    except Exception as e:
        print(f"Fehler beim Laden der Farbeinstellungen: {e}")
        # Fallback-Werte bei Fehler
        return {
            'primary': '259 94% 51%',
            'secondary': '314 100% 47%',
            'accent': '174 60% 51%'
        }

def save_color_setting(key, value):
    """Speichert eine Farbeinstellung in der Datenbank"""
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            """, (f'{key}_color', value))
            conn.commit()
    except Exception as e:
        print(f"Fehler beim Speichern der Farbeinstellung: {e}")