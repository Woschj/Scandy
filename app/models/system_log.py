from datetime import datetime
from .database import Database, BaseModel

class SystemLog(BaseModel):
    TABLE_NAME = 'system_logs'

    @staticmethod
    def log(level, message, details=None):
        """Fügt einen neuen Log-Eintrag hinzu"""
        sql = '''
        INSERT INTO system_logs (level, message, details, timestamp)
        VALUES (?, ?, ?, ?)
        '''
        params = (level, message, details, datetime.now())
        return Database.query(sql, params)

    @staticmethod
    def get_recent(limit=100):
        """Holt die neuesten Log-Einträge"""
        sql = '''
        SELECT * FROM system_logs 
        ORDER BY timestamp DESC 
        LIMIT ?
        '''
        return Database.query(sql, [limit])

    @staticmethod
    def get_by_level(level, limit=100):
        """Holt Log-Einträge eines bestimmten Levels"""
        sql = '''
        SELECT * FROM system_logs 
        WHERE level = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
        '''
        return Database.query(sql, [level, limit])

    @staticmethod
    def clear_old_logs(days=30):
        """Löscht alte Log-Einträge"""
        sql = '''
        DELETE FROM system_logs 
        WHERE timestamp < datetime('now', '-? days')
        '''
        return Database.query(sql, [days])