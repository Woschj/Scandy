from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import Database
from app.models.worker import Worker
from app.utils.decorators import admin_required

bp = Blueprint('workers', __name__)

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

@bp.route('/workers/<barcode>')
def details(barcode):
    worker = Worker.get_by_barcode(barcode)
    if worker:
        lending_history = Database.query('''
            SELECT l.*, t.name as tool_name
            FROM lendings l
            JOIN tools t ON l.tool_barcode = t.barcode
            WHERE l.worker_barcode = ?
            ORDER BY l.lent_at DESC
        ''', [barcode])
        return render_template('worker_details.html', 
                             worker=worker, 
                             history=lending_history)
    flash('Mitarbeiter nicht gefunden', 'error')
    return redirect(url_for('workers.index'))

@bp.route('/workers/<barcode>/edit', methods=['GET', 'POST'])
@admin_required
def edit(barcode):
    worker = Worker.get_by_barcode(barcode)
    if not worker:
        flash('Mitarbeiter nicht gefunden', 'error')
        return redirect(url_for('workers.index'))
    
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        department = request.form.get('department', '')
        email = request.form.get('email', '')
        
        try:
            Database.query(
                '''UPDATE workers 
                   SET firstname = ?, lastname = ?, 
                       department = ?, email = ? 
                   WHERE barcode = ?''',
                [firstname, lastname, department, email, barcode]
            )
            flash('Mitarbeiter erfolgreich aktualisiert', 'success')
            return redirect(url_for('workers.details', barcode=barcode))
        except Exception as e:
            flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return render_template('admin/edit_worker.html', worker=worker)

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