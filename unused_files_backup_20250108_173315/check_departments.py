import sqlite3
import os

def check_departments():
    """Überprüft die Abteilungen in der Datenbank"""
    print("\n=== DETAILLIERTE ABTEILUNGSPRÜFUNG ===")
    db_path = os.path.join('app', 'database', 'inventory.db')
    print(f"Datenbank: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n1. Alle Einträge in settings mit department_:")
    cursor.execute('SELECT * FROM settings WHERE key LIKE "department_%"')
    settings_depts = cursor.fetchall()
    for dept in settings_depts:
        print(f"Key: {dept['key']}, Value: {dept['value']}, Description: {dept['description']}")
    
    print("\n2. Alle Abteilungen in workers:")
    cursor.execute('SELECT DISTINCT department FROM workers WHERE department IS NOT NULL AND deleted = 0')
    worker_depts = cursor.fetchall()
    for dept in worker_depts:
        print(f"Department: {dept['department']}")
        
        # Zeige Mitarbeiter in dieser Abteilung
        cursor.execute('''
            SELECT firstname || " " || lastname as name 
            FROM workers 
            WHERE department = ? AND deleted = 0
        ''', [dept['department']])
        workers = cursor.fetchall()
        print(f"  Mitarbeiter ({len(workers)}):")
        for worker in workers:
            print(f"    - {worker['name']}")
    
    conn.close()

if __name__ == "__main__":
    check_departments() 