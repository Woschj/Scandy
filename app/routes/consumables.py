from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from app.models.database import get_db_connection
from app.utils.decorators import login_required, admin_required
from app.models.consumable import Consumable

bp = Blueprint('consumables', __name__, url_prefix='/consumables')

@bp.route('/')
@login_required
def index():
    filter_type = request.args.get('filter')
    consumables = Consumable.get_all_active()
    if filter_type == 'low_stock':
        consumables = [c for c in consumables if c['bestand'] <= c['mindestbestand'] and c['bestand'] > 0]
    elif filter_type == 'out_of_stock':
        consumables = [c for c in consumables if c['bestand'] == 0]
    return render_template('consumables.html', consumables=consumables)

@bp.route('/<barcode>')
@login_required
def details(barcode):
    with get_db_connection() as conn:
        consumable = conn.execute('''
            SELECT * FROM consumables WHERE barcode = ?
        ''', (barcode,)).fetchone()
        
        history = conn.execute('''
            SELECT 
                ch.*,
                w.name as worker_name,
                w.lastname as worker_lastname
            FROM consumables_history ch
            LEFT JOIN workers w ON ch.worker_barcode = w.barcode
            WHERE ch.consumable_barcode = ?
            ORDER BY ch.timestamp DESC
        ''', (barcode,)).fetchall()
        
        return render_template('consumable_details.html', 
                             consumable=consumable, 
                             history=history)

@bp.route('/edit/<barcode>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(barcode):
    try:
        with get_db_connection() as conn:
            if request.method == 'POST':
                data = request.form
                conn.execute('''
                    UPDATE consumables 
                    SET bezeichnung = ?,
                        typ = ?,
                        ort = ?,
                        bestand = ?,
                        einheit = ?,
                        mindestbestand = ?
                    WHERE barcode = ?
                ''', (
                    data['bezeichnung'],
                    data['typ'],
                    data['ort'],
                    data['bestand'],
                    data['einheit'],
                    data['mindestbestand'],
                    barcode
                ))
                conn.commit()
                flash('Verbrauchsmaterial erfolgreich aktualisiert.', 'success')
                return redirect(url_for('consumables.details', barcode=barcode))
            
            consumable = conn.execute('''
                SELECT * FROM consumables 
                WHERE barcode = ? AND deleted = 0
            ''', (barcode,)).fetchone()
            
            if not consumable:
                flash('Verbrauchsmaterial nicht gefunden.', 'error')
                return redirect(url_for('consumables.index'))
            
            return render_template('edit_consumable.html', consumable=consumable)
    except Exception as e:
        current_app.logger.error(f'Fehler beim Bearbeiten: {str(e)}')
        return str(e), 500

@bp.route('/update_stock', methods=['POST'])
@login_required
def update_stock():
    try:
        data = request.get_json()
        barcode = data.get('barcode')
        quantity = data.get('quantity')
        action = data.get('action')
        worker_barcode = data.get('worker_barcode')
        
        with get_db_connection() as conn:
            # Aktuelle Menge prüfen
            current = conn.execute('SELECT bestand FROM consumables WHERE barcode = ?', 
                                (barcode,)).fetchone()
            
            if not current:
                return {'success': False, 'message': 'Verbrauchsmaterial nicht gefunden'}, 404
            
            new_quantity = current['bestand']
            if action == 'add':
                new_quantity += quantity
            elif action == 'remove':
                if current['bestand'] < quantity:
                    return {'success': False, 'message': 'Nicht genügend Bestand'}, 400
                new_quantity -= quantity
            
            # Bestand aktualisieren
            conn.execute('UPDATE consumables SET bestand = ? WHERE barcode = ?', 
                       (new_quantity, barcode))
            
            # Historie eintragen
            conn.execute('''
                INSERT INTO consumables_history 
                (consumable_barcode, action, worker_barcode, quantity, timestamp)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (barcode, action, worker_barcode, quantity))
            
            conn.commit()
            return {'success': True, 'new_quantity': new_quantity}
    except Exception as e:
        current_app.logger.error(f'Fehler bei Bestandsaktualisierung: {str(e)}')
        return {'success': False, 'message': str(e)}, 500

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    """Neues Verbrauchsmaterial hinzufügen"""
    if request.method == 'POST':
        barcode = request.form.get('barcode')
        name = request.form.get('name')
        description = request.form.get('description')
        quantity = request.form.get('quantity', type=int)
        min_quantity = request.form.get('min_quantity', type=int)
        
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO consumables (barcode, name, description, quantity, min_quantity, created_at, deleted)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
            ''', [barcode, name, description, quantity, min_quantity])
            conn.commit()
            
        flash('Verbrauchsmaterial erfolgreich hinzugefügt', 'success')
        return redirect(url_for('consumables.index'))
        
    return render_template('consumables/add.html')

# ... weitere Routen ...