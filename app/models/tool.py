from app.models.database import get_db

class Tool:
    @staticmethod
    def count_active():
        db = get_db('inventory.db')
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM tools WHERE deleted = 0 OR deleted IS NULL')
        return cursor.fetchone()[0] 

    @staticmethod
    def get_all_active():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM tools WHERE deleted = 0 OR deleted IS NULL')
        return cursor.fetchall()

    @staticmethod
    def count_by_status(status):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM tools WHERE status = ? AND (deleted = 0 OR deleted IS NULL)', (status,))
        return cursor.fetchone()[0]

    @staticmethod
    def get_current_lendings():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT t.name as tool_name, w.name as worker_name, l.lending_time
            FROM lendings l
            JOIN tools t ON l.tool_barcode = t.barcode
            JOIN workers w ON l.worker_barcode = w.barcode
            WHERE l.return_time IS NULL
            ORDER BY l.lending_time DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]