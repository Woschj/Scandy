from PIL import Image
import cairosvg
import io
import os

def svg_to_ico():
    # Pfade
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    svg_path = os.path.join(project_dir, 'app', 'static', 'images', 'scandy-logo.svg')
    ico_path = os.path.join(project_dir, 'electron', 'assets', 'icon.ico')
    
    # Erstelle assets Ordner falls nicht vorhanden
    os.makedirs(os.path.dirname(ico_path), exist_ok=True)
    
    # Konvertiere SVG zu PNG in verschiedenen Größen
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        png_data = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)
        img = Image.open(io.BytesIO(png_data))
        images.append(img)
    
    # Speichere als ICO
    images[0].save(ico_path, format='ICO', sizes=[(s,s) for s in sizes], append_images=images[1:])
    print(f"Icon erstellt: {ico_path}")

if __name__ == '__main__':
    svg_to_ico() 