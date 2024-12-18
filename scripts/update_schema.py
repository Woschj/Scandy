import sqlite3
from pathlib import Path

def update_schema():
    """Aktualisiert das Datenbankschema"""
    db_path = Path(__file__).parent.parent / 'database' / 'inventory.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Füge consumable_usage Tabelle hinzu...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consumable_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consumable_id) REFERENCES consumables(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Schema-Update abgeschlossen!")

if __name__ == '__main__':
    update_schema() 
    