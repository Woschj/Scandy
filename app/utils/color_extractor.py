from PIL import Image
import colorsys
from flask import current_app
import os

def extract_dominant_color(logo_path=None):
    """Gibt die Standardfarben zurück oder extrahiert sie aus einem Bild (nicht SVG)"""
    try:
        if logo_path and not logo_path.lower().endswith('.svg'):
            full_path = os.path.join(current_app.static_folder, 'images', logo_path)
            img = Image.open(full_path).convert('RGBA')
            
            # Zu RGB konvertieren und Pixel analysieren
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            
            colors = rgb_img.getcolors(rgb_img.size[0] * rgb_img.size[1])
            if colors:
                filtered_colors = [
                    (count, color) for count, color in colors 
                    if color != (255, 255, 255) and color != (0, 0, 0)
                    and sum(color) < (255 * 3 - 50)
                ]
                
                if filtered_colors:
                    dominant_color = max(filtered_colors)[1]
                    primary = '#{:02x}{:02x}{:02x}'.format(*dominant_color)
                    
                    h, s, v = colorsys.rgb_to_hsv(*[x/255 for x in dominant_color])
                    secondary_rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, max(0, s-0.1), min(1, v+0.1)))
                    secondary = '#{:02x}{:02x}{:02x}'.format(*secondary_rgb)
                    
                    accent_rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, min(1, s+0.1), max(0, v-0.1)))
                    accent = '#{:02x}{:02x}{:02x}'.format(*accent_rgb)
                    
                    return {
                        'primary': primary,
                        'secondary': secondary,
                        'accent': accent
                    }
        
        # Standardfarben zurückgeben
        return {
            'primary': '#FF4D8D',    # Scandy Pink
            'secondary': '#FF99B9',  # Helles Pink
            'accent': '#FF3333'      # Akzentfarbe
        }
        
    except Exception as e:
        current_app.logger.error(f"Fehler bei der Farbextraktion: {str(e)}")
        return {
            'primary': '#FF4D8D',
            'secondary': '#FF99B9',
            'accent': '#FF3333'
        }