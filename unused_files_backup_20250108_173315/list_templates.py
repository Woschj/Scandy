import os

def list_templates(start_path='app/templates'):
    """
    Listet alle Template-Dateien und ihre Struktur auf
    """
    print("\nGefundene Templates:")
    print("===================")
    
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = '  ' * level
        folder = os.path.basename(root)
        
        if level > 0:
            print(f'{indent[:-2]}📁 {folder}/')
        
        subindent = '  ' * (level + 1)
        for file in files:
            if file.endswith('.html'):
                print(f'{subindent}📄 {file}')

if __name__ == "__main__":
    try:
        list_templates()
    except FileNotFoundError:
        print("Fehler: Template-Verzeichnis nicht gefunden!")
        print("Bitte stellen Sie sicher, dass Sie das Skript im richtigen Verzeichnis ausführen.") 