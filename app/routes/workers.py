from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.database import Database
from app.models.worker import Worker
from app.routes.auth import admin_required
from datetime import datetime

bp = Blueprint('workers', __name__, url_prefix='/inventory/workers')

@bp.route('/workers')
def index():
    workers = Worker.get_all_with_lendings()
    return render_template('workers.html', workers=workers)

@bp.route('/workers/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        barcode = request.form['barcode']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        department = request.form.get('department', '')
        email = request.form.get('email', '')
        
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
            
    return render_template('admin/add_worker.html')

@bp.route('/<barcode>', methods=['GET'])
def details(barcode):
    worker = Database.query('SELECT * FROM workers WHERE barcode = ? AND deleted = 0', [barcode], one=True)
    if not worker:
        flash('Mitarbeiter nicht gefunden', 'error')
        return redirect(url_for('workers.index'))

    # Aktuelle Ausleihen
    current_lendings = Database.query('''
        SELECT 
            l.*,
            COALESCE(t.name, c.name) as item_name,
            CASE 
                WHEN t.id IS NOT NULL THEN 'Werkzeug'
                ELSE 'Verbrauchsmaterial'
            END as item_type,
            l.quantity as amount_display,
            datetime(l.lent_at, 'localtime') as formatted_checkout_time
        FROM lendings l
        LEFT JOIN tools t ON l.tool_barcode = t.barcode
        LEFT JOIN consumables c ON l.consumable_barcode = c.barcode
        WHERE l.worker_barcode = ? 
        AND l.returned_at IS NULL
    ''', [barcode])

    # Ausleihverlauf
    lending_history = Database.query('''
        SELECT 
            l.*,
            COALESCE(t.name, c.name) as item_name,
            CASE 
                WHEN t.id IS NOT NULL THEN 'Werkzeug'
                ELSE 'Verbrauchsmaterial'
            END as item_type,
            l.quantity as amount_display,
            datetime(l.lent_at, 'localtime') as formatted_checkout_time,
            datetime(l.returned_at, 'localtime') as formatted_return_time
        FROM lendings l
        LEFT JOIN tools t ON l.tool_barcode = t.barcode
        LEFT JOIN consumables c ON l.consumable_barcode = c.barcode
        WHERE l.worker_barcode = ? 
        AND l.returned_at IS NOT NULL
        ORDER BY l.lent_at DESC
    ''', [barcode])

    return render_template('worker_details.html', 
                         worker=worker,
                         current_lendings=current_lendings,
                         lending_history=lending_history)

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

@bp.route('/workers/<barcode>/delete', methods=['POST'])
@admin_required
def delete(barcode):
    try:
        Database.query(
            'UPDATE workers SET deleted = 1 WHERE barcode = ?',
            [barcode]
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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