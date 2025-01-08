import sqlite3
import os

def delete_department(name):
    print(f"=== DELETING DEPARTMENT {name} ===")
    db_path = os.path.join('app', 'database', 'inventory.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfe ob Mitarbeiter in der Abteilung sind
        cursor.execute('SELECT COUNT(*) FROM workers WHERE department = ? AND deleted = 0', [name])
        worker_count = cursor.fetchone()[0]
        
        if worker_count > 0:
            print(f"Fehler: Abteilung hat noch {worker_count} aktive Mitarbeiter")
            return False
            
        # Lösche die Abteilung
        cursor.execute('DELETE FROM settings WHERE key = ?', [f"department_{name}"])
        conn.commit()
        
        # Prüfe ob die Löschung erfolgreich war
        cursor.execute('SELECT COUNT(*) FROM settings WHERE key = ?', [f"department_{name}"])
        if cursor.fetchone()[0] == 0:
            print(f"Abteilung {name} wurde erfolgreich gelöscht")
            return True
        else:
            print(f"Fehler: Abteilung {name} konnte nicht gelöscht werden")
            return False
            
    finally:
        conn.close()

if __name__ == "__main__":
    delete_department("1235") 