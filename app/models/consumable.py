from .database import BaseModel, Database

class Consumable(BaseModel):
    TABLE_NAME = 'consumables'

    @staticmethod
    def get_all_with_stock():
        sql = '''
        SELECT c.*, 
               c.quantity as current_stock,
               CASE 
                   WHEN c.quantity <= c.min_quantity THEN 'low'
                   ELSE 'ok'
               END as stock_status
        FROM consumables c
        WHERE c.deleted = 0
        ORDER BY c.name
        '''
        return Database.query(sql)