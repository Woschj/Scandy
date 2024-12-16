from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import Database
from app.models.consumable import Consumable
from app.utils.decorators import admin_required

bp = Blueprint('consumables', __name__, url_prefix='/consumables')

@bp.route('/')
def index():
    consumables = Database.query('''
        SELECT c.*, 
               c.quantity as current_stock,
               CASE 
                   WHEN c.quantity <= c.min_quantity THEN 'low'
                   ELSE 'ok'
               END as stock_status
        FROM consumables c
        WHERE c.deleted = 0
        ORDER BY c.name
    ''')
    return render_template('consumables.html', consumables=consumables)

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        barcode = request.form['barcode']
        name = request.form['name']
        description = request.form.get('description', '')
        quantity = int(request.form.get('quantity', 0))
        min_quantity = int(request.form.get('min_quantity', 0))
        
        try:
            Database.query(
                '''INSERT INTO consumables 
                   (barcode, name, description, quantity, min_quantity) 
                   VALUES (?, ?, ?, ?, ?)''',
                [barcode, name, description, quantity, min_quantity]
            )
            flash('Verbrauchsmaterial erfolgreich hinzugefügt', 'success')
            return redirect(url_for('consumables.index'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
            
    return render_template('admin/add_consumable.html')

@bp.route('/<barcode>')
def details(barcode):
    consumable = Consumable.get_by_barcode(barcode)
    if consumable:
        history = Database.query('''
            SELECT ch.*, w.firstname || ' ' || w.lastname as worker_name
            FROM consumables_history ch
            LEFT JOIN workers w ON ch.worker_barcode = w.barcode
            WHERE ch.consumable_barcode = ?
            ORDER BY ch.timestamp DESC
        ''', [barcode])
        return render_template('consumable_details.html', 
                             consumable=consumable, 
                             history=history)
    flash('Verbrauchsmaterial nicht gefunden', 'error')
    return redirect(url_for('consumables.index'))

@bp.route('/<barcode>/edit', methods=['GET', 'POST'])
@admin_required
def edit(barcode):
    consumable = Consumable.get_by_barcode(barcode)
    if not consumable:
        flash('Verbrauchsmaterial nicht gefunden', 'error')
        return redirect(url_for('consumables.index'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        quantity = int(request.form.get('quantity', 0))
        min_quantity = int(request.form.get('min_quantity', 0))
        
        try:
            Database.query(
                '''UPDATE consumables 
                   SET name = ?, description = ?, 
                       quantity = ?, min_quantity = ? 
                   WHERE barcode = ?''',
                [name, description, quantity, min_quantity, barcode]
            )
            flash('Verbrauchsmaterial erfolgreich aktualisiert', 'success')
            return redirect(url_for('consumables.details', barcode=barcode))
        except Exception as e:
            flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return render_template('admin/edit_consumable.html', consumable=consumable)

@bp.route('/<barcode>/delete', methods=['POST'])
@admin_required
def delete(barcode):
    try:
        Database.query(
            'UPDATE consumables SET deleted = 1 WHERE barcode = ?',
            [barcode]
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ... weitere Routen ...