from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, abort
from ..models.database import Database
from ..utils.decorators import login_required, admin_required
from datetime import datetime

bp = Blueprint('consumables', __name__, url_prefix='/consumables')

@bp.route('/<string:barcode>')
@login_required
def detail(barcode):
    """Zeigt die Details eines Verbrauchsmaterials"""
    consumable = Database.query('''
        SELECT * FROM consumables WHERE barcode = ? AND deleted = 0
    ''', [barcode], one=True)
    
    if not consumable:
        flash('Verbrauchsmaterial nicht gefunden', 'error')
        return redirect(url_for('consumables.index'))
    
    # Hole vordefinierte Kategorien und Standorte aus den Einstellungen
    categories = Database.get_categories('consumables')
    locations = Database.get_locations('consumables')
    
    # Hole Bestandsänderungen
    history = Database.query('''
        SELECT 
            'Bestandsänderung' as action_type,
            strftime('%d.%m.%Y %H:%M', cu.used_at) as action_date,
            CASE 
                WHEN cu.worker_barcode = 'admin' THEN 'Admin'
                ELSE w.firstname || ' ' || w.lastname 
            END as worker_name,
            CASE
                WHEN cu.worker_barcode = 'admin' THEN cu.quantity
                ELSE -ABS(cu.quantity)  -- Für Mitarbeiter immer negativ machen
            END as quantity
        FROM consumable_usages cu
        LEFT JOIN workers w ON cu.worker_barcode = w.barcode
        WHERE cu.consumable_barcode = ?
        ORDER BY cu.used_at DESC
    ''', [barcode])
    
    return render_template('consumables/details.html',
                         consumable=consumable,
                         categories=[c['name'] for c in categories],
                         locations=[l['name'] for l in locations],
                         history=history)

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
    
    # Hole vordefinierte Kategorien und Standorte aus den Einstellungen
    categories = Database.get_categories('consumables')
    locations = Database.get_locations('consumables')
    
    return render_template('consumables/add.html',
                         categories=[c['name'] for c in categories],
                         locations=[l['name'] for l in locations])

@bp.route('/<barcode>/adjust-stock', methods=['POST'])
@login_required
def adjust_stock(barcode):
    """Passt den Bestand eines Verbrauchsmaterials an"""
    try:
        quantity = request.form.get('quantity', type=int)
        
        if quantity is None:
            return jsonify({'success': False, 'message': 'Menge muss angegeben werden'}), 400
            
        with Database.get_db() as conn:
            # Aktuellen Bestand abrufen
            current = conn.execute('''
                SELECT quantity FROM consumables 
                WHERE barcode = ? AND deleted = 0
            ''', [barcode]).fetchone()
            
            if not current:
                return jsonify({'success': False, 'message': 'Verbrauchsmaterial nicht gefunden'}), 404
            
            # Bestand aktualisieren
            conn.execute('''
                UPDATE consumables 
                SET quantity = ?,
                    modified_at = CURRENT_TIMESTAMP
                WHERE barcode = ?
            ''', [quantity, barcode])
            
            # Änderung protokollieren
            conn.execute('''
                INSERT INTO consumable_usages 
                (consumable_barcode, worker_barcode, quantity, used_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', [barcode, 'admin', quantity - current['quantity']])
            
            conn.commit()
            
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Fehler bei der Bestandsanpassung: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/<barcode>')
@login_required
def details(barcode):
    """Zeigt die Details eines Verbrauchsmaterials"""
    consumable = Database.query('''
        SELECT * FROM consumables 
        WHERE barcode = ? AND deleted = 0
    ''', [barcode], one=True)
    
    if not consumable:
        abort(404)
        
    # Hole vordefinierte Kategorien und Standorte aus den Einstellungen
    categories = Database.get_categories('consumables')
    locations = Database.get_locations('consumables')
    
    # Entnahme-Historie
    history = Database.query('''
        SELECT 
            'Bestandsänderung' as action_type,
            strftime('%d.%m.%Y %H:%M', cu.used_at) as action_date,
            CASE 
                WHEN cu.worker_barcode = 'admin' THEN 'Admin'
                ELSE w.firstname || ' ' || w.lastname 
            END as worker_name,
            CASE
                WHEN cu.worker_barcode = 'admin' THEN cu.quantity
                ELSE -ABS(cu.quantity)  -- Für Mitarbeiter immer negativ machen
            END as quantity
        FROM consumable_usages cu
        LEFT JOIN workers w ON cu.worker_barcode = w.barcode
        WHERE cu.consumable_barcode = ?
        ORDER BY cu.used_at DESC
    ''', [barcode])
    
    return render_template('consumables/details.html',
                         consumable=consumable,
                         categories=[c['name'] for c in categories],
                         locations=[l['name'] for l in locations],
                         history=history)