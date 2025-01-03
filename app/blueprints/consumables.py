from flask import Blueprint, render_template, abort
from app.database import Database

bp = Blueprint('consumables', __name__)

@bp.route('/')
def index():
    items = Database.query('''
        SELECT *, 
            CASE 
                WHEN quantity <= 0 THEN 'empty'
                ELSE 'available'
            END as stock_status
        FROM consumables
        WHERE deleted = 0
    ''')
    return render_template('consumables/index.html', items=items)

@bp.route('/<uuid>')
def detail(uuid):
    # Verbrauchsmaterial-Details laden
    consumable = Database.query('''
        SELECT * FROM consumables 
        WHERE uuid = ? AND deleted = 0
    ''', [uuid], one=True)
    
    if not consumable:
        abort(404)
        
    # Letzte Entnahmen (z.B. letzte 5)
    recent_usage = Database.query('''
        SELECT cu.*, w.firstname || ' ' || w.lastname as worker_name
        FROM consumable_usage cu
        JOIN workers w ON w.barcode = cu.worker_barcode
        WHERE cu.consumable_barcode = ?
        ORDER BY cu.used_at DESC
        LIMIT 5
    ''', [consumable['barcode']])
    
    # Komplette Historie
    usage_history = Database.query('''
        SELECT cu.*, w.firstname || ' ' || w.lastname as worker_name
        FROM consumable_usage cu
        JOIN workers w ON w.barcode = cu.worker_barcode
        WHERE cu.consumable_barcode = ?
        ORDER BY cu.used_at DESC
    ''', [consumable['barcode']])
    
    return render_template('consumables/details.html',
                         consumable=consumable,
                         recent_usage=recent_usage,
                         usage_history=usage_history) 