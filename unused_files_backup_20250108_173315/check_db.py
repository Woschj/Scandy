import sqlite3
import os

def check_departments():
    print("=== CHECKING DATABASE CONTENTS ===")
    db_path = os.path.join('app', 'database', 'inventory.db')
    print(f"Database path: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n=== Departments in settings table ===")
    cursor.execute('SELECT * FROM settings WHERE key LIKE "department_%"')
    departments = cursor.fetchall()
    for dept in departments:
        print(dept)
        
    print("\n=== Workers and their departments ===")
    cursor.execute('SELECT DISTINCT department FROM workers WHERE department IS NOT NULL AND deleted = 0')
    worker_depts = cursor.fetchall()
    for dept in worker_depts:
        print(dept)
        
    conn.close()

if __name__ == "__main__":
    check_departments() 