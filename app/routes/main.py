from flask import Blueprint, render_template
from ..models.database import Database
from ..utils.system_structure import get_system_structure

# Kein URL-Präfix für den Main-Blueprint
bp = Blueprint('main', __name__, url_prefix='')

@bp.route('/')
def index():
    """Zeigt die Hauptseite mit Statistiken"""
    try:
        # Werkzeug-Statistiken
        tool_stats = {
            'total': Database.query('SELECT COUNT(*) as count FROM tools WHERE deleted = 0', one=True)['count'],
            'available': Database.query('''
                SELECT COUNT(*) as count 
                FROM tools 
                WHERE deleted = 0 
                AND status != 'defekt' 
                AND barcode NOT IN (
                    SELECT tool_barcode 
                    FROM lendings 
                    WHERE returned_at IS NULL
                )
            ''', one=True)['count'],
            'defect': Database.query("SELECT COUNT(*) as count FROM tools WHERE deleted = 0 AND status = 'defekt'", one=True)['count']
        }

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
                           tool_stats={'total': 0, 'available': 0, 'defect': 0},
                           consumable_stats={'total': 0, 'sufficient': 0, 'warning': 0, 'critical': 0},
                           worker_stats={'total': 0, 'by_department': []})

@bp.route('/about')
def about():
    """Zeigt die About-Seite mit Systemdokumentation"""
    return render_template('about.html') 