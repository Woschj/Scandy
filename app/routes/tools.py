from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import Database
from app.utils.decorators import admin_required, login_required
from datetime import datetime

bp = Blueprint('tools', __name__, url_prefix='/tools')

@bp.route('/')
def index():
    """Zeigt alle aktiven Werkzeuge"""
    tools = Database.query('''
        SELECT t.*,
               l.lent_at,
               w.firstname || ' ' || w.lastname as lent_to,
               CASE 
                   WHEN t.status = 'defect' THEN 'defect'
                   WHEN l.id IS NOT NULL THEN 'lent'
                   ELSE 'available'
               END as current_status
        FROM tools t
        LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
        LEFT JOIN workers w ON l.worker_barcode = w.barcode
        WHERE t.deleted = 0
        ORDER BY t.name
    ''')
    
    # Debug-Ausgabe
    if tools:
        print("Beispiel-Tool:", dict(tools[0]))
    
    categories = Database.query('''
        SELECT DISTINCT category FROM tools
        WHERE deleted = 0 AND category IS NOT NULL
        ORDER BY category
    ''')
    
    locations = Database.query('''
        SELECT DISTINCT location FROM tools
        WHERE deleted = 0 AND location IS NOT NULL
        ORDER BY location
    ''')
    
    return render_template('tools/index.html',
                         tools=tools,
                         categories=[c['category'] for c in categories],
                         locations=[l['location'] for l in locations])

@bp.route('/<string:uuid>')
@login_required
def detail(uuid):
    """Zeigt die Detailansicht eines Werkzeugs"""
    try:
        # Hole Werkzeug mit aktueller Ausleihe
        tool = Database.query('''
            SELECT t.*, 
                   l.lent_at,
                   w.firstname || ' ' || w.lastname as current_worker,
                   CASE 
                       WHEN t.status = 'defect' THEN 'defekt'
                       WHEN l.id IS NOT NULL THEN 'ausgeliehen'
                       ELSE 'verfügbar'
                   END as status
            FROM tools t
            LEFT JOIN lendings l ON t.barcode = l.tool_barcode 
                AND l.returned_at IS NULL
            LEFT JOIN workers w ON l.worker_barcode = w.barcode
            WHERE t.uuid = ? AND t.deleted = 0
        ''', [uuid], one=True)
        
        if not tool:
            return redirect(url_for('tools.index'))
            
        # Hole Ausleihhistorie
        lending_history = Database.query('''
            SELECT l.*,
                   w.firstname || ' ' || w.lastname as worker_name,
                   w.department as worker_department
            FROM lendings l
            JOIN workers w ON l.worker_barcode = w.barcode
            WHERE l.tool_barcode = ?
            ORDER BY l.lent_at DESC
        ''', [tool['barcode']])
        
        # Füge Historie zum Werkzeug hinzu
        tool['lending_history'] = lending_history
        
        # Aktuelle Ausleihe
        tool['current_lending'] = None
        if tool['status'] == 'ausgeliehen':
            tool['current_lending'] = {
                'worker_name': tool['current_worker']
            }
            
        return render_template('tools/detail.html', tool=tool)
        
    except Exception as e:
        print(f"Fehler beim Laden der Werkzeugdetails: {str(e)}")
        return redirect(url_for('tools.index'))

@bp.route('/<int:id>/update', methods=['POST'])
@admin_required
def update(id):
    """Aktualisiert ein Werkzeug"""
    try:
        data = request.form
        
        Database.query('''
            UPDATE tools 
            SET name = ?,
                barcode = ?,
                category = ?,
                location = ?,
                description = ?,
                modified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', [
            data.get('name'),
            data.get('barcode'),
            data.get('category'),
            data.get('location'),
            data.get('description'),
            id
        ])
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Werkzeugs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/<int:id>/delete', methods=['POST'])
@admin_required
def delete(id):
    """Löscht ein Werkzeug (Soft Delete)"""
    try:
        Database.query('''
            UPDATE tools 
            SET deleted = 1,
                deleted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', [id])
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Fehler beim Löschen des Werkzeugs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    """Neues Werkzeug hinzufügen"""
    if request.method == 'POST':
        name = request.form.get('name')
        barcode = request.form.get('barcode')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        status = request.form.get('status', 'Verfügbar')
        
        try:
            Database.query('''
                INSERT INTO tools 
                (name, barcode, description, category, location, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', [name, barcode, description, category, location, status])
            
            flash('Werkzeug erfolgreich hinzugefügt', 'success')
            return redirect(url_for('tools.index'))
            
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
    
    # Hole existierende Kategorien und Orte für Vorschläge
    categories = Database.query('''
        SELECT DISTINCT category FROM tools 
        WHERE deleted = 0 AND category IS NOT NULL
        ORDER BY category
    ''')
    
    locations = Database.query('''
        SELECT DISTINCT location FROM tools
        WHERE deleted = 0 AND location IS NOT NULL
        ORDER BY location
    ''')
    
    return render_template('admin/add_tool.html',
                         categories=[c['category'] for c in categories],
                         locations=[l['location'] for l in locations])

# Weitere Tool-Routen...