import sqlite3
from pathlib import Path

def check_table_structure():
    db_path = Path(__file__).parent.parent / 'database' / 'inventory.db'
    print(f"Verwende Datenbank: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nPrüfe Struktur der consumable_usage Tabelle:")
    cursor.execute("PRAGMA table_info(consumable_usage)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    print("\nPrüfe die ersten 5 Einträge:")
    cursor.execute("""
        SELECT cu.*, w.firstname || ' ' || w.lastname as worker_name
        FROM consumable_usage cu
        LEFT JOIN workers w ON cu.worker_barcode = w.barcode
        LIMIT 5
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    conn.close()

if __name__ == '__main__':
    check_table_structure() 