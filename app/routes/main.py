from flask import Blueprint, render_template
from ..models.database import Database
from ..utils.system_structure import get_system_structure

# Kein URL-Präfix für den Main-Blueprint
bp = Blueprint('main', __name__, url_prefix='')

@bp.route('/')
def index():
    """Zeigt die Hauptseite mit Statistiken"""
    try:
        # Werkzeug-Statistiken mit verbesserter Abfrage
        tool_stats = Database.query('''
            WITH valid_tools AS (
                SELECT barcode 
                FROM tools 
                WHERE deleted = 0
            )
            SELECT 
                COUNT(*) as total,
                SUM(CASE 
                    WHEN NOT EXISTS (
                        SELECT 1 FROM lendings l 
                        WHERE l.tool_barcode = t.barcode 
                        AND l.returned_at IS NULL
                    ) AND status = 'verfügbar' THEN 1 
                    ELSE 0 
                END) as available,
                (
                    SELECT COUNT(DISTINCT l.tool_barcode) 
                    FROM lendings l
                    JOIN valid_tools vt ON l.tool_barcode = vt.barcode
                    WHERE l.returned_at IS NULL
                ) as lent,
                SUM(CASE WHEN status = 'defekt' THEN 1 ELSE 0 END) as defect
            FROM tools t
            WHERE t.deleted = 0
        ''', one=True)
        
        # Debug-Ausgabe
        print("Tool Stats:", tool_stats)
        
        # Verbrauchsmaterial-Statistiken
        consumable_stats = {
            'total': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0', one=True)['count'],
            'sufficient': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity >= min_quantity', one=True)['count'],
            'warning': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity < min_quantity AND quantity >= min_quantity * 0.5', one=True)['count'],
            'critical': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity < min_quantity * 0.5', one=True)['count']
        }

        # Mitarbeiter-Statistiken
        worker_stats = {
            'total': Database.query('SELECT COUNT(*) as count FROM workers WHERE deleted = 0', one=True)['count'],
            'by_department': Database.query('''
                SELECT department as name, COUNT(*) as count 
                FROM workers 
                WHERE deleted = 0 AND department IS NOT NULL 
                GROUP BY department 
                ORDER BY department
            ''')
        }

        return render_template('index.html',
                           tool_stats=tool_stats,
                           consumable_stats=consumable_stats,
                           worker_stats=worker_stats)
                           
    except Exception as e:
        print(f"Fehler beim Laden der Startseite: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return render_template('index.html',
                           tool_stats={'total': 0, 'available': 0, 'lent': 0, 'defect': 0},
                           consumable_stats={'total': 0, 'sufficient': 0, 'warning': 0, 'critical': 0},
                           worker_stats={'total': 0, 'by_department': []})

@bp.route('/about')
def about():
    """Zeigt die About-Seite mit Systemdokumentation"""
    return render_template('about.html') 