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

@bp.route('/<barcode>', methods=['GET', 'POST'])
@login_required
def details(barcode):
    """Details eines Mitarbeiters anzeigen und bearbeiten"""
    try:
        if request.method == 'POST':
            data = request.form
            
            with Database.get_db() as conn:
                conn.execute('''
                    UPDATE workers 
                    SET firstname = ?,
                        lastname = ?,
                        department = ?,
                        modified_at = CURRENT_TIMESTAMP
                    WHERE barcode = ? AND deleted = 0
                ''', [
                    data.get('firstname'),
                    data.get('lastname'),
                    data.get('department'),
                    barcode
                ])
                conn.commit()
            
            return jsonify({'success': True})
        
        # GET-Anfrage: Details anzeigen
        with Database.get_db() as conn:
            worker = conn.execute('''
                SELECT * FROM workers 
                WHERE barcode = ? AND deleted = 0
            ''', [barcode]).fetchone()
            
            if not worker:
                return jsonify({'success': False, 'message': 'Mitarbeiter nicht gefunden'}), 404
            
            # Ausleihhistorie laden
            lending_history = conn.execute('''
                SELECT l.*, t.name as tool_name
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode AND t.deleted = 0
                WHERE l.worker_barcode = ?
                ORDER BY l.lent_at DESC
            ''', [barcode]).fetchall()
            
            # Verbrauchsmaterial-Historie laden
            usage_history = conn.execute('''
                SELECT cu.*, c.name as consumable_name
                FROM consumable_usages cu
                JOIN consumables c ON cu.consumable_barcode = c.barcode AND c.deleted = 0
                WHERE cu.worker_barcode = ?
                ORDER BY cu.used_at DESC
            ''', [barcode]).fetchall()
            
            return render_template('workers/details.html',
                               worker=worker,
                               lending_history=lending_history,
                               usage_history=usage_history)
                               
    except Exception as e:
        print(f"Fehler bei Mitarbeiter-Details: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

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