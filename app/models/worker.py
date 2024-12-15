from app.models.database import get_db_connection

class Worker:
    @staticmethod
    def count_active():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM workers WHERE deleted = 0 OR deleted IS NULL')
            return cursor.fetchone()[0]

    @staticmethod
    def get_all_active():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workers WHERE deleted = 0 OR deleted IS NULL')
            return cursor.fetchall()

    @staticmethod
    def count_with_active_lendings():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(DISTINCT worker_barcode) 
                FROM lendings 
                WHERE return_time IS NULL
            ''')
            return cursor.fetchone()[0]

    @staticmethod
    def get_by_barcode(barcode):
        with get_db_connection() as conn:
            worker = conn.execute('''
                SELECT barcode, name, lastname, bereich, email
                FROM workers 
                WHERE barcode = ? AND deleted = 0
            ''', (barcode,)).fetchone()
        return worker

    @staticmethod
    def update(barcode, name, lastname, bereich=None, email=None):
        with get_db_connection() as conn:
            conn.execute('''
                UPDATE workers 
                SET name = ?, 
                    lastname = ?, 
                    bereich = ?,
                    email = ?
                WHERE barcode = ?
            ''', (name, lastname, bereich, email, barcode))
            conn.commit()