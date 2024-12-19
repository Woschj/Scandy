import sqlite3
import os
from pathlib import Path

def migrate_consumable_usage():
    """Migriert die consumable_usage Tabelle von worker_id zu worker_barcode"""
    
    # Datenbankpfad ermitteln
    db_path = Path(__file__).parent.parent / 'database' / 'inventory.db'
    print(f"Verwende Datenbank: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starte Migration...")
        
        # Prüfe ob worker_barcode bereits existiert
        cursor.execute("PRAGMA table_info(consumable_usage)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'worker_barcode' in columns:
            print("worker_barcode Spalte existiert bereits.")
            if 'worker_id' not in columns:
                print("Migration scheint bereits abgeschlossen zu sein.")
                return
        
        # Backup der alten Tabelle
        print("1. Erstelle Backup...")
        cursor.execute('''
            CREATE TABLE consumable_usage_backup AS 
            SELECT * FROM consumable_usage
        ''')
        
        # Alte Spalte entfernen und neue Tabelle erstellen
        print("2. Erstelle neue Tabellenstruktur...")
        cursor.execute('''
            CREATE TABLE consumable_usage_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consumable_id INTEGER NOT NULL,
                worker_barcode TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (consumable_id) REFERENCES consumables(id),
                FOREIGN KEY (worker_barcode) REFERENCES workers(barcode)
            )
        ''')
        
        # Daten in neue Tabelle kopieren
        print("3. Kopiere Daten in neue Tabelle...")
        cursor.execute('''
            INSERT INTO consumable_usage_new 
                (id, consumable_id, worker_barcode, quantity, used_at)
            SELECT 
                id, consumable_id, worker_barcode, quantity, used_at 
            FROM consumable_usage
        ''')
        
        # Überprüfen ob alle Einträge aktualisiert wurden
        cursor.execute('''
            SELECT COUNT(*) FROM consumable_usage 
            WHERE worker_barcode IS NULL
        ''')
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"WARNUNG: {null_count} Einträge konnten nicht migriert werden!")
            raise Exception("Migration unvollständig")
        
        # Alte Tabelle durch neue ersetzen
        print("4. Ersetze alte Tabelle...")
        cursor.execute('DROP TABLE consumable_usage')
        cursor.execute('ALTER TABLE consumable_usage_new RENAME TO consumable_usage')
        
        # Commit und Aufräumen
        conn.commit()
        print("Migration erfolgreich abgeschlossen!")
        
        # Backup löschen wenn alles geklappt hat
        print("5. Lösche Backup-Tabelle...")
        cursor.execute('DROP TABLE consumable_usage_backup')
        conn.commit()
        
    except Exception as e:
        print(f"Fehler bei der Migration: {str(e)}")
        print("Stelle Backup wieder her...")
        try:
            cursor.execute('DROP TABLE IF EXISTS consumable_usage')
            cursor.execute('ALTER TABLE consumable_usage_backup RENAME TO consumable_usage')
            conn.commit()
            print("Backup wiederhergestellt!")
        except Exception as restore_error:
            print(f"Fehler beim Wiederherstellen des Backups: {str(restore_error)}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_consumable_usage() 