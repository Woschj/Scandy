from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app.database import Database  # Direkt aus app.database importieren
import logging

bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)

@bp.route('/departments')
@login_required
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

@bp.route('/manual-lending', methods=['GET', 'POST'])
@login_required
def manual_lending():
    try:
        # Basis-Abfragen wie in den anderen Templates
        tools = Database.query('''
            SELECT t.*, 
                   CASE 
                       WHEN l.id IS NULL THEN 'Verfügbar'
                       ELSE 'Ausgeliehen'
                   END as status
            FROM tools t
            LEFT JOIN lendings l ON t.barcode = l.tool_barcode 
                AND l.returned_at IS NULL
            WHERE t.deleted = 0
            ORDER BY t.name
        ''')
        print(f"DEBUG: Found {len(tools)} tools")
        
        workers = Database.query('''
            SELECT * 
            FROM workers
            WHERE deleted = 0
            ORDER BY firstname, lastname
        ''')
        print(f"DEBUG: Found {len(workers)} workers")
        
        consumables = Database.query('''
            SELECT *
            FROM consumables 
            WHERE deleted = 0
                AND quantity > 0
            ORDER BY name
        ''')
        print(f"DEBUG: Found {len(consumables)} consumables")

        return render_template('admin/manual_lending.html',
                            tools=tools,
                            workers=workers,
                            consumables=consumables,
                            current_lendings=[])

    except Exception as e:
        print(f"ERROR in manual_lending: {str(e)}")
        return f"Error: {str(e)}", 500