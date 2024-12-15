from datetime import datetime
from app.models.database import get_db

class SystemLog:
    @staticmethod
    def log(level, message, user_id=None, action=None):
        """
        Fügt einen neuen Log-Eintrag hinzu
        """
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO system_logs (timestamp, level, message, user_id, action)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now(), level, message, user_id, action))
        
        db.commit()
    
    @staticmethod
    def get_logs(limit=100):
        """
        Holt die letzten Log-Einträge
        """
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT * FROM system_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()