from .database import BaseModel, Database

class Tool(BaseModel):
    TABLE_NAME = 'tools'

    @staticmethod
    def get_all_with_status():
        sql = '''
        SELECT t.*, 
               l.worker_barcode,
               l.lent_at,
               l.returned_at,
               w.firstname || ' ' || w.lastname as current_borrower
        FROM tools t
        LEFT JOIN (
            SELECT tool_barcode, worker_barcode, lent_at, returned_at
            FROM lendings l1
            WHERE NOT EXISTS (
                SELECT 1 FROM lendings l2
                WHERE l2.tool_barcode = l1.tool_barcode
                AND l2.lent_at > l1.lent_at
            )
        ) l ON t.barcode = l.tool_barcode
        LEFT JOIN workers w ON l.worker_barcode = w.barcode
        WHERE t.deleted = 0
        ORDER BY t.name
        '''
        return Database.query(sql)