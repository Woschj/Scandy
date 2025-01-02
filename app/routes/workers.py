from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.database import Database
from app.models.worker import Worker
from app.utils.decorators import login_required, admin_required
from datetime import datetime

bp = Blueprint('workers', __name__, url_prefix='/workers')

@bp.route('/')
def index():
    """Mitarbeiter-Übersicht"""
    try:
        # Debug-Ausgabe
        print("\n=== WORKERS INDEX ===")
        
        # Hole alle aktiven Mitarbeiter mit Ausleihzähler
        workers = Database.query('''
            SELECT w.*,
                   COUNT(DISTINCT l.id) as active_lendings
            FROM workers w
            LEFT JOIN lendings l ON w.barcode = l.worker_barcode AND l.returned_at IS NULL
            WHERE w.deleted = 0
            GROUP BY w.id, w.barcode, w.firstname, w.lastname, w.department, w.email,
                     w.created_at, w.modified_at, w.deleted, w.deleted_at, w.sync_status
            ORDER BY w.lastname, w.firstname
        ''')
        
        print(f"Gefundene Mitarbeiter: {len(workers)}")
        if workers:
            print("Erster Datensatz:", dict(workers[0]))
        
        # Hole alle Abteilungen für Filter
        departments = Database.query('''
            SELECT DISTINCT department FROM workers
            WHERE deleted = 0 AND department IS NOT NULL
            ORDER BY department
        ''')
        
        print(f"Gefundene Abteilungen: {[d['department'] for d in departments]}")
        
        return render_template('workers/index.html',
                             workers=workers,
                             departments=[d['department'] for d in departments],
                             is_admin=session.get('is_admin', False))
                             
    except Exception as e:
        print(f"Fehler beim Laden der Mitarbeiter: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('Fehler beim Laden der Mitarbeiter', 'error')
        return redirect(url_for('index'))

@bp.route('/add', methods=['GET', 'POST'])
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
            return render_template('workers/add.html', departments=departments)
        
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
            
    return render_template('workers/add.html', departments=departments)

@bp.route('/<barcode>')
def details(barcode):
    """Zeigt Details eines Mitarbeiters"""
    worker = Database.query('SELECT * FROM workers WHERE barcode = ? AND deleted = 0', [barcode], one=True)
    
    if not worker:
        flash('Mitarbeiter nicht gefunden', 'error')
        return redirect(url_for('workers.index'))
        
    # Aktuelle Ausleihen
    active_lendings = Database.query('''
        SELECT
            t.name as tool_name,
            t.barcode as tool_barcode,
            l.lent_at
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ?
        AND l.returned_at IS NULL
        ORDER BY l.lent_at DESC
    ''', [barcode])
    
    # Historie
    history = Database.query('''
        SELECT
            t.name as item_name,
            t.barcode as item_barcode,
            l.lent_at,
            l.returned_at,
            'Werkzeug' as type,
            NULL as quantity
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ?
        AND l.returned_at IS NOT NULL
        
        UNION ALL
        
        SELECT
            c.name as item_name,
            c.barcode as item_barcode,
            cu.used_at as lent_at,
            cu.used_at as returned_at,
            'Verbrauchsmaterial' as type,
            cu.quantity
        FROM consumable_usages cu
        JOIN consumables c ON cu.consumable_barcode = c.barcode
        WHERE cu.worker_barcode = ?
        ORDER BY lent_at DESC
    ''', [barcode, barcode])
    
    return render_template('workers/details.html',
                         worker=worker,
                         active_lendings=active_lendings,
                         history=history)

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