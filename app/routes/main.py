from flask import Blueprint, render_template
from ..models.database import Database
from ..utils.system_structure import get_system_structure

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Zeigt die Startseite mit Kurzanleitung und wichtigen Hinweisen"""
    try:
        # Einfache Statistiken für die Startseite
        tool_stats = {
            'total': Database.query('SELECT COUNT(*) as count FROM tools WHERE deleted = 0', one=True)['count'],
            'available': Database.query('''
                SELECT COUNT(*) as count 
                FROM tools 
                WHERE deleted = 0 
                AND status != 'defect' 
                AND barcode NOT IN (
                    SELECT tool_barcode 
                    FROM lendings 
                    WHERE returned_at IS NULL
                )
            ''', one=True)['count'],
            'defect': Database.query("SELECT COUNT(*) as count FROM tools WHERE status = 'defect' AND deleted = 0", one=True)['count']
        }
        
        consumable_stats = {
            'total': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0', one=True)['count'],
            'sufficient': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity >= min_quantity', one=True)['count'],
            'warning': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity < min_quantity AND quantity >= min_quantity * 0.5', one=True)['count'],
            'critical': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity < min_quantity * 0.5', one=True)['count']
        }
        
        worker_stats = {
            'total': Database.query('SELECT COUNT(*) as count FROM workers WHERE deleted = 0', one=True)['count'],
            'by_department': Database.query('''
                SELECT 
                    department as name,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM workers WHERE deleted = 0), 1) as percentage
                FROM workers 
                WHERE deleted = 0 
                GROUP BY department
                ORDER BY count DESC
            ''')
        }
        
        return render_template('index.html',
                             tool_stats=tool_stats,
                             consumable_stats=consumable_stats,
                             worker_stats=worker_stats)
                             
    except Exception as e:
        print(f"Fehler beim Laden der Startseite: {str(e)}")
        # Fallback: Render template ohne Statistiken
        return render_template('index.html') 

@bp.route('/about')
def about():
    """Zeigt die About-Seite mit Systemdokumentation"""
    # Entferne alle dynamischen Variablen aus dem Template
    return render_template('about.html') 