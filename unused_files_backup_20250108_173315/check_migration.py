import sqlite3

def check_and_migrate():
    conn = sqlite3.connect('instance/scandy.db')
    cursor = conn.cursor()
    
    # Zeige alle Tabellen
    print("Vorhandene Tabellen:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"- {table[0]}")
        
    # Prüfe ob tool_status_changes existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tool_status_changes';")
    if not cursor.fetchone():
        print("\nErstelle tool_status_changes Tabelle...")
        
        # Führe Migration aus
        with open('app/migrations/008_add_tool_status_changes.sql', 'r') as f:
            sql = f.read()
            cursor.executescript(sql)
            conn.commit()
            print("Migration erfolgreich ausgeführt!")
    else:
        print("\ntool_status_changes Tabelle existiert bereits")
        
    # Zeige Struktur der tool_status_changes Tabelle
    print("\nStruktur der tool_status_changes Tabelle:")
    cursor.execute("PRAGMA table_info(tool_status_changes);")
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
        
    conn.close()

if __name__ == '__main__':
    check_and_migrate() 