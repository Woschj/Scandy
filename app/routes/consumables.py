from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.database import Database
from app.utils.decorators import admin_required

# Blueprint mit korrektem Namen definieren
bp = Blueprint('consumables', __name__, url_prefix='/consumables')

@bp.route('/')
def index():
    """Verbrauchsmaterialien-Übersicht"""
    try:
        # Vereinfachte Query ohne die problematische JOIN
        consumables = Database.query('''
            SELECT * FROM consumables
            WHERE deleted = 0
            ORDER BY name
        ''')
        
        # Hole Filter-Optionen
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
        
        return render_template('consumables/index.html',
                             items=consumables,
                             categories=[c['category'] for c in categories],
                             locations=[l['location'] for l in locations])
        
    except Exception as e:
        print(f"Fehler in consumables.index: {str(e)}")  # Debug-Ausgabe
        flash(f'Fehler beim Laden der Verbrauchsmaterialien: {str(e)}', 'error')
        return redirect(url_for('tools.index'))

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
        try:
            history = Database.query('''
                SELECT 
                    w.firstname || ' ' || w.lastname as worker_name,
                    strftime('%d.%m.%Y %H:%M', cu.used_at) as timestamp,
                    cu.quantity as amount,
                    'Ausgabe' as action
                FROM consumable_usage cu
                JOIN workers w ON cu.worker_barcode = w.barcode
                WHERE cu.consumable_id = (
                    SELECT id FROM consumables WHERE barcode = ?
                )
                ORDER BY cu.used_at DESC
            ''', [barcode])
        except Exception as e:
            print(f"Fehler beim Abrufen der Historie: {e}")  # Debug-Ausgabe
            history = []
            
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
        try:
            Database.query('''
                UPDATE consumables 
                SET name = ?,
                    description = ?,
                    quantity = ?,
                    min_quantity = ?,
                    location = ?,
                    category = ?
                WHERE barcode = ?
            ''', [
                request.form['name'],
                request.form.get('description', ''),
                int(request.form.get('quantity', 0)),
                int(request.form.get('min_quantity', 0)),
                request.form.get('location', ''),
                request.form.get('category', ''),
                barcode
            ])
            
            flash('Verbrauchsmaterial erfolgreich aktualisiert', 'success')
            return redirect(url_for('consumables.details', barcode=barcode))
        except Exception as e:
            flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return render_template('consumable_details.html', consumable=consumable)

@bp.route('/<barcode>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete(barcode):
    try:
        print(f"Lösche Verbrauchsmaterial: {barcode}")
        result = Database.soft_delete('consumables', barcode)
        print(f"Lösch-Ergebnis: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Fehler beim Löschen: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        })