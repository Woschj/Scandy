from flask import Flask
from app.models.database import Database

def create_minimal_app():
    app = Flask(__name__)
    return app

def get_schema():
    return [
        # Neue Tabelle für Verbrauchsmaterial-Nutzung
        """
        CREATE TABLE IF NOT EXISTS consumable_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_barcode TEXT NOT NULL,
            worker_barcode TEXT NOT NULL,
            amount INTEGER NOT NULL DEFAULT 1,
            used_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted INTEGER NOT NULL DEFAULT 0,
            deleted_at DATETIME,
            FOREIGN KEY (consumable_barcode) REFERENCES consumables (barcode),
            FOREIGN KEY (worker_barcode) REFERENCES workers (barcode)
        )
        """
    ]

def main():
    print("Initialisiere Datenbank...")
    try:
        app = create_minimal_app()
        with app.app_context():
            with Database.get_db() as db:
                cursor = db.cursor()
                
                # Führe alle Schema-Statements aus
                for statement in get_schema():
                    print(f"Führe aus: {statement[:60]}...")  # Zeigt die ersten 60 Zeichen
                    cursor.execute(statement)
                
                db.commit()
                
        print("Datenbank erfolgreich initialisiert!")
    except Exception as e:
        print(f"Fehler bei der Initialisierung: {str(e)}")

if __name__ == "__main__":
    main() 