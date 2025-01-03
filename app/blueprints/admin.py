from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from flask_admin import admin_required
from app.models import Database

@bp.route('/departments')
@login_required
@admin_required
def departments():
    departments = Database.query('''
        SELECT d.*,
               COUNT(w.id) as worker_count
        FROM departments d
        LEFT JOIN workers w ON w.department = d.name AND w.deleted = 0
        WHERE d.deleted = 0
        GROUP BY d.id
        ORDER BY d.name
    ''')
    return render_template('admin/departments.html', departments=departments)

@bp.route('/departments/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    name = request.form.get('name')
    if not name:
        flash('Bitte geben Sie einen Namen ein', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Prüfen ob die Abteilung bereits existiert
    existing = Database.query('''
        SELECT DISTINCT department 
        FROM workers 
        WHERE department = ? AND deleted = 0
    ''', [name], one=True)
    
    if existing:
        flash('Diese Abteilung existiert bereits', 'error')
    else:
        # Dummy-Eintrag erstellen und gleich wieder löschen
        # So haben wir die Abteilung in der Auswahlliste
        Database.execute('''
            INSERT INTO workers 
            (firstname, lastname, barcode, department, deleted) 
            VALUES (?, ?, ?, ?, ?)
        ''', ['DUMMY', 'DUMMY', 'DUMMY', name, 1])
        flash('Abteilung wurde hinzugefügt', 'success')
    
    return redirect(url_for('admin.dashboard'))

@bp.route('/departments/<name>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_department(name):
    # Prüfen ob noch Mitarbeiter in der Abteilung sind
    count = Database.query('''
        SELECT COUNT(*) as count 
        FROM workers 
        WHERE department = ? AND deleted = 0
    ''', [name], one=True)['count']
    
    if count > 0:
        return jsonify({
            'message': 'Es sind noch Mitarbeiter dieser Abteilung zugeordnet'
        }), 400
    
    return '', 204 