from app import create_app
from app.models.database import init_db
from app.utils.structure_viewer import print_database_structure, print_app_structure

# Datenbank initialisieren
init_db()

app = create_app()

if __name__ == '__main__':
    print("\n=== System-Start-Information ===\n")
    print_database_structure()
    print_app_structure()
    print("\n=== Server-Start ===\n")
    app.run(debug=True, host='0.0.0.0', port=5000) 