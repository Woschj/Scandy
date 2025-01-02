from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import Database
from app.utils.decorators import admin_required
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

@bp.route('/<barcode>')
def details(barcode):
    """Zeigt Details eines Werkzeugs"""
    tool = Database.query('''
        SELECT t.*, 
               l.lent_at,
               w.firstname || ' ' || w.lastname as current_borrower,
               w.department as borrower_department
        FROM tools t
        LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
        LEFT JOIN workers w ON l.worker_barcode = w.barcode
        WHERE t.barcode = ? AND t.deleted = 0
    ''', [barcode], one=True)
    
    if not tool:
        flash('Werkzeug nicht gefunden', 'error')
        return redirect(url_for('tools.index'))
        
    return render_template('tools/details_modal.html', tool=tool)

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