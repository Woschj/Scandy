from .database import BaseModel, Database

class Consumable(BaseModel):
    TABLE_NAME = 'consumables'

    @staticmethod
    def get_all():
        sql = '''
        SELECT 
            c.*,
            CASE 
                WHEN c.quantity <= c.min_quantity THEN 'Nachbestellen'
                ELSE 'OK'
            END as stock_status
        FROM consumables c
        WHERE c.deleted = 0
        ORDER BY c.name
        '''
        return Database.query(sql)

    @staticmethod
    def get_by_barcode(barcode):
        sql = '''
        SELECT 
            c.*,
            CASE 
                WHEN c.quantity <= c.min_quantity THEN 'Nachbestellen'
                ELSE 'OK'
            END as stock_status
        FROM consumables c
        WHERE c.barcode = ? 
        AND c.deleted = 0
        '''
        with Database.get_db() as conn:
            result = conn.execute(sql, [barcode]).fetchone()
            return result