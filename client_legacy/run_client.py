from app import create_app
from app.config import Config

# Aktiviere Client-Modus
Config.init_client(server_url='http://localhost:5000')  # Kann in den Einstellungen geändert werden

app = create_app()

if __name__ == '__main__':
    app.run(port=5000) 