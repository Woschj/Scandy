from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from ..models.database import Database
from ..utils.decorators import login_required, admin_required
from datetime import datetime

bp = Blueprint('consumables', __name__, url_prefix='/consumables')

@bp.route('/<string:barcode>')
@login_required
def detail(barcode):
    """Zeigt die Detailansicht eines Verbrauchsmaterials"""
    try:
        # Hole Verbrauchsmaterial mit Barcode
        consumable = Database.query('''
            SELECT c.*, 
                   CASE 
                       WHEN c.quantity >= c.min_quantity THEN 'verfügbar'
                       WHEN c.quantity > 0 THEN 'knapp'
                       ELSE 'leer'
                   END as status
            FROM consumables c
            WHERE c.barcode = ? AND c.deleted = 0
        ''', [barcode], one=True)
        
        if not consumable:
            return redirect(url_for('consumables.index'))
            
        # Hole Nutzungshistorie
        usage_history = Database.query('''
            SELECT cu.*,
                   w.firstname || ' ' || w.lastname as worker_name,
                   w.department as worker_department
            FROM consumable_usages cu
            JOIN workers w ON cu.worker_barcode = w.barcode
            WHERE cu.consumable_barcode = ?
            ORDER BY cu.used_at DESC
        ''', [barcode])
        
        # Hole die letzten 5 Entnahmen
        recent_usage = Database.query('''
            SELECT cu.*,
                   w.firstname || ' ' || w.lastname as worker_name,
                   w.department as worker_department
            FROM consumable_usages cu
            JOIN workers w ON cu.worker_barcode = w.barcode
            WHERE cu.consumable_barcode = ?
            ORDER BY cu.used_at DESC
            LIMIT 5
        ''', [barcode])
            
        return render_template('consumables/details.html',
                            consumable=consumable,
                            usage_history=usage_history,
                            recent_usage=recent_usage)
        
    except Exception as e:
        print(f"Fehler beim Laden der Verbrauchsmaterial-Details: {str(e)}")
        return redirect(url_for('consumables.index'))

@bp.route('/<int:id>/update', methods=['POST'])
@admin_required
def update(id):
    """Aktualisiert ein Verbrauchsmaterial"""
    try:
        data = request.form
        
        Database.query('''
            UPDATE consumables 
            SET name = ?,
                barcode = ?,
                category = ?,
                location = ?,
                description = ?,
                quantity = ?,
                min_quantity = ?,
                modified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', [
            data.get('name'),
            data.get('barcode'),
            data.get('category'),
            data.get('location'),
            data.get('description'),
            data.get('quantity', type=int),
            data.get('min_quantity', type=int),
            id
        ])
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Verbrauchsmaterials: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/<int:id>/delete', methods=['POST'])
@admin_required
def delete(id):
    """Löscht ein Verbrauchsmaterial (Soft Delete)"""
    try:
        Database.query('''
            UPDATE consumables 
            SET deleted = 1,
                deleted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', [id])
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Fehler beim Löschen des Verbrauchsmaterials: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/')
def index():
    """Zeigt alle aktiven Verbrauchsmaterialien"""
    consumables = Database.query('''
        SELECT c.*,
               ROUND(CAST(c.quantity AS FLOAT) / NULLIF(c.min_quantity, 0) * 100) as stock_percentage,
               CASE
                   WHEN c.quantity >= c.min_quantity THEN 'sufficient'
                   WHEN c.quantity >= c.min_quantity * 0.5 THEN 'warning'
                   ELSE 'critical'
               END as stock_status
        FROM consumables c
        WHERE c.deleted = 0
        ORDER BY c.name
    ''')
    
    # Kategorien für Filter
    categories = Database.query('''
        SELECT DISTINCT category FROM consumables
        WHERE deleted = 0 AND category IS NOT NULL
        ORDER BY category
    ''')
    
    # Standorte für Filter
    locations = Database.query('''
        SELECT DISTINCT location FROM consumables
        WHERE deleted = 0 AND location IS NOT NULL
        ORDER BY location
    ''')
    
    return render_template('consumables/index.html',
                         consumables=consumables,
                         categories=[c['category'] for c in categories],
                         locations=[l['location'] for l in locations])

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    """Neues Verbrauchsmaterial hinzufügen"""
    if request.method == 'POST':
        name = request.form.get('name')
        barcode = request.form.get('barcode')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        quantity = request.form.get('quantity', type=int)
        min_quantity = request.form.get('min_quantity', type=int)
        
        try:
            Database.query('''
                INSERT INTO consumables 
                (name, barcode, description, category, location, quantity, min_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [name, barcode, description, category, location, quantity, min_quantity])
            
            flash('Verbrauchsmaterial erfolgreich hinzugefügt', 'success')
            return redirect(url_for('consumables.index'))
            
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
    
    # Hole existierende Kategorien und Orte für Vorschläge
    categories = Database.query('''
        SELECT DISTINCT category FROM consumables 
        WHERE deleted = 0 AND category IS NOT NULL
        ORDER BY category
    ''')
    
    locations = Database.query('''
        SELECT DISTINCT location FROM consumables
        WHERE deleted = 0 AND location IS NOT NULL
        ORDER BY location
    ''')
    
    return render_template('consumables/add.html',
                         categories=[c['category'] for c in categories],
                         locations=[l['location'] for l in locations])