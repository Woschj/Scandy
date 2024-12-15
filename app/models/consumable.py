from app.models.database import get_db

class Consumable:
    @staticmethod
    def count_active():
        db = get_db('inventory.db')
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM consumables WHERE deleted = 0 OR deleted IS NULL')
        return cursor.fetchone()[0] 

    @staticmethod
    def get_all_active():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM consumables WHERE deleted = 0 OR deleted IS NULL')
        return cursor.fetchall() 

    @staticmethod
    def count_low_stock():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM consumables 
            WHERE bestand <= mindestbestand 
            AND bestand > 0 
            AND (deleted = 0 OR deleted IS NULL)
        ''')
        return cursor.fetchone()[0]

    @staticmethod
    def count_out_of_stock():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM consumables 
            WHERE bestand = 0 
            AND (deleted = 0 OR deleted IS NULL)
        ''')
        return cursor.fetchone()[0]