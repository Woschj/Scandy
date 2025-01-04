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

@bp.route('/<barcode>')
def detail(barcode):
    """Zeigt die Detailansicht eines Werkzeugs"""
    try:
        # Hole Werkzeug mit allen relevanten Informationen
        tool = Database.query('''
            SELECT t.*, 
                   l.lent_at,
                   w.firstname || ' ' || w.lastname as lent_to,
                   tsc.reason as status_reason
            FROM tools t
            LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
            LEFT JOIN workers w ON l.worker_barcode = w.barcode
            LEFT JOIN (
                SELECT tool_barcode, reason
                FROM tool_status_changes
                WHERE id = (
                    SELECT id FROM tool_status_changes 
                    WHERE tool_barcode = ? 
                    ORDER BY created_at DESC LIMIT 1
                )
            ) tsc ON t.barcode = tsc.tool_barcode
            WHERE t.barcode = ? AND t.deleted = 0
        ''', [barcode, barcode], one=True)

        if tool is None:
            abort(404)

        # Kombinierter Verlauf aus Ausleihen und Statusänderungen
        history = Database.query('''
            SELECT 
                l.lent_at as action_date,
                'Ausleihe/Rückgabe' as action_type,
                CASE 
                    WHEN l.returned_at IS NULL THEN 'Ausgeliehen an ' || w.firstname || ' ' || w.lastname
                    ELSE 'Zurückgegeben von ' || w.firstname || ' ' || w.lastname
                END as description,
                NULL as reason
            FROM lendings l
            JOIN workers w ON l.worker_barcode = w.barcode 
            WHERE l.tool_barcode = ?
            UNION ALL
            SELECT 
                created_at as action_date,
                'Statusänderung' as action_type,
                'Status geändert zu: ' || new_status as description,
                reason
            FROM tool_status_changes
            WHERE tool_barcode = ?
            ORDER BY action_date DESC
        ''', [barcode, barcode])

        return render_template('tools/details.html', tool=tool, history=history)
        
    except Exception as e:
        print(f"Fehler beim Laden der Werkzeugdetails: {str(e)}")
        flash('Fehler beim Laden der Werkzeugdetails', 'error')
        return redirect(url_for('tools.index'))

@bp.route('/<int:id>/update', methods=['GET', 'POST'])
@admin_required
def update(id):
    """Aktualisiert ein Werkzeug"""
    try:
        if request.method == 'GET':
            # Hole Werkzeug für das Formular
            tool = Database.query('''
                SELECT * FROM tools 
                WHERE id = ? AND deleted = 0
            ''', [id], one=True)
            
            if tool is None:
                flash('Werkzeug nicht gefunden', 'error')
                return redirect(url_for('tools.index'))
                
            return render_template('tools/edit.html', tool=tool)
            
        # POST-Anfrage
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
        
        flash('Werkzeug erfolgreich aktualisiert', 'success')
        return redirect(url_for('tools.detail', barcode=data.get('barcode')))
        
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Werkzeugs: {str(e)}")
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
        return redirect(url_for('tools.index'))

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

@bp.route('/<string:barcode>/status', methods=['POST'])
@login_required
def change_status(barcode):
    """Ändert den Status eines Werkzeugs"""
    try:
        status = request.form.get('status')
        reason = request.form.get('reason', '')  # Optional, leerer String wenn nicht angegeben
        
        if not status:
            return jsonify({
                'success': False,
                'message': 'Status muss angegeben werden'
            }), 400
            
        # Prüfe ob das Werkzeug existiert und hole aktuellen Status
        tool = Database.query('''
            SELECT * FROM tools 
            WHERE barcode = ? AND deleted = 0
        ''', [barcode], one=True)
        
        if not tool:
            return jsonify({
                'success': False,
                'message': 'Werkzeug nicht gefunden'
            }), 404
            
        # Prüfe ob das Werkzeug ausgeliehen ist
        if status == 'defekt':
            lending = Database.query('''
                SELECT * FROM lendings
                WHERE tool_barcode = ? AND returned_at IS NULL
            ''', [barcode], one=True)
            
            if lending:
                return jsonify({
                    'success': False,
                    'message': 'Werkzeug muss zuerst zurückgegeben werden'
                }), 400
        
        # Statusänderung protokollieren
        Database.query('''
            INSERT INTO tool_status_changes 
            (tool_barcode, old_status, new_status, reason)
            VALUES (?, ?, ?, ?)
        ''', [barcode, tool['status'], status, reason])
        
        # Status aktualisieren
        Database.query('''
            UPDATE tools 
            SET status = ?,
                modified_at = datetime('now'),
                sync_status = 'pending'
            WHERE barcode = ?
        ''', [status, barcode])
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Fehler beim Ändern des Status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500

# Weitere Tool-Routen...