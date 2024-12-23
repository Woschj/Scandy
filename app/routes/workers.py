from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.database import Database
from app.models.worker import Worker
from app.utils.decorators import login_required, admin_required
from datetime import datetime

bp = Blueprint('workers', __name__, url_prefix='/workers')

@bp.route('/')
@admin_required
def index():
    workers = Worker.get_all_with_lendings()
    return render_template('workers.html', workers=workers)

@bp.route('/workers/add', methods=['GET', 'POST'])
@admin_required
def add():
    departments = [
        'Medien und Digitales',
        'Technik',
        'Kaufmännisches',
        'Service',
        'APE',
        'Mitarbeiter'
    ]
    
    if request.method == 'POST':
        barcode = request.form['barcode']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        department = request.form.get('department', '')
        email = request.form.get('email', '')
        
        if department not in departments:
            flash('Ungültige Abteilung ausgewählt', 'error')
            return render_template('admin/add_worker.html', departments=departments)
        
        try:
            Database.query(
                '''INSERT INTO workers 
                   (barcode, firstname, lastname, department, email) 
                   VALUES (?, ?, ?, ?, ?)''',
                [barcode, firstname, lastname, department, email]
            )
            flash('Mitarbeiter erfolgreich hinzugefügt', 'success')
            return redirect(url_for('workers.index'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
            
    return render_template('admin/add_worker.html', departments=departments)

@bp.route('/<barcode>', methods=['GET'])
def details(barcode):
    departments = [
        'Medien und Digitales',
        'Technik',
        'Kaufmännisches',
        'Service',
        'APE',
        'Mitarbeiter'
    ]
    
    worker = Database.query('SELECT * FROM workers WHERE barcode = ? AND deleted = 0', [barcode], one=True)
    if not worker:
        flash('Mitarbeiter nicht gefunden', 'error')
        return redirect(url_for('workers.index'))

    # Hole aktuelle Ausleihen
    current_lendings = Database.query('''
        SELECT 
            t.name as tool_name,
            t.barcode as tool_barcode,
            strftime('%d.%m.%Y %H:%M', l.lent_at) as lent_at,
            'Werkzeug' as item_type,
            1 as amount_display
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ? 
        AND l.returned_at IS NULL
        ORDER BY l.lent_at DESC
    ''', [barcode])

    # Hole Ausleihhistorie
    lending_history = Database.query('''
        SELECT 
            t.name as tool_name,
            t.barcode as tool_barcode,
            strftime('%d.%m.%Y %H:%M', l.lent_at) as lent_at,
            strftime('%d.%m.%Y %H:%M', l.returned_at) as returned_at,
            'Werkzeug' as item_type,
            NULL as amount_display
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ?
        AND l.returned_at IS NOT NULL
        UNION ALL
        SELECT 
            c.name as tool_name,
            c.barcode as tool_barcode,
            strftime('%d.%m.%Y %H:%M', cu.used_at) as lent_at,
            strftime('%d.%m.%Y %H:%M', cu.used_at) as returned_at,
            'Verbrauchsmaterial' as item_type,
            NULL as amount_display
        FROM consumable_usage cu
        JOIN consumables c ON cu.consumable_id = c.id
        JOIN workers w ON cu.worker_id = w.id
        WHERE w.barcode = ?
        ORDER BY lent_at DESC
    ''', [barcode, barcode])

    return render_template('worker_details.html', 
                         worker=worker,
                         current_lendings=current_lendings,
                         lending_history=lending_history,
                         departments=departments)

@bp.route('/<barcode>/edit', methods=['POST'])
@admin_required
def edit(barcode):
    try:
        Database.query('''
            UPDATE workers 
            SET firstname = ?,
                lastname = ?,
                email = ?,
                department = ?
            WHERE barcode = ?
        ''', [
            request.form['firstname'],
            request.form['lastname'],
            request.form.get('email', ''),
            request.form.get('department', ''),
            barcode
        ])
        flash('Mitarbeiter erfolgreich aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return redirect(url_for('workers.details', barcode=barcode))

@bp.route('/<barcode>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete(barcode):
    try:
        print(f"Lösche Mitarbeiter: {barcode}")
        result = Database.soft_delete('workers', barcode)
        print(f"Lösch-Ergebnis: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Fehler beim Löschen: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        })

@bp.route('/workers/search')
def search():
    query = request.args.get('q', '')
    try:
        workers = Database.query('''
            SELECT * FROM workers 
            WHERE (firstname LIKE ? OR lastname LIKE ? OR barcode LIKE ?) 
            AND deleted = 0
        ''', [f'%{query}%', f'%{query}%', f'%{query}%'])
        return jsonify([dict(worker) for worker in workers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500