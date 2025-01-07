from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.database import Database
from app.utils.decorators import admin_required, login_required
from datetime import datetime
import logging

# Explizit URL-Präfix setzen
bp = Blueprint('tools', __name__, url_prefix='/tools')

@bp.route('/')
def index():
    """Zeigt alle aktiven Werkzeuge"""
    try:
        with Database.get_db() as conn:
            # Debug: Prüfe aktive Ausleihen
            active_lendings = conn.execute('''
                SELECT tool_barcode, worker_barcode, lent_at 
                FROM lendings 
                WHERE returned_at IS NULL
            ''').fetchall()
            print("Aktive Ausleihen:", [dict(l) for l in active_lendings])

            tools = conn.execute('''
                SELECT t.*,
                       CASE 
                           WHEN l.tool_barcode IS NOT NULL THEN 'ausgeliehen'
                           WHEN t.status = 'defekt' THEN 'defekt'
                           ELSE 'verfügbar'
                       END as current_status,
                       w.firstname || ' ' || w.lastname as lent_to,
                       l.lent_at as lending_date,
                       t.location,
                       t.category
                FROM tools t
                LEFT JOIN (
                    SELECT tool_barcode, worker_barcode, lent_at
                    FROM lendings
                    WHERE returned_at IS NULL
                ) l ON t.barcode = l.tool_barcode
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.deleted = 0
                ORDER BY t.name
            ''').fetchall()
            
            # Debug-Ausgabe
            if tools:
                print("Beispiel-Tool:", dict(tools[0]))
                for tool in tools:
                    tool_dict = dict(tool)
                    print(f"Tool {tool_dict['barcode']}: Status = {tool_dict['current_status']}, Ausgeliehen an = {tool_dict.get('lent_to', 'niemanden')}")
            
            categories = conn.execute('''
                SELECT DISTINCT category FROM tools
                WHERE deleted = 0 AND category IS NOT NULL
                ORDER BY category
            ''').fetchall()
            
            locations = conn.execute('''
                SELECT DISTINCT location FROM tools
                WHERE deleted = 0 AND location IS NOT NULL
                ORDER BY location
            ''').fetchall()
            
            return render_template('tools/index.html',
                               tools=tools,
                               categories=[c['category'] for c in categories],
                               locations=[l['location'] for l in locations])
                               
    except Exception as e:
        print(f"Fehler beim Laden der Werkzeuge: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('Fehler beim Laden der Werkzeuge', 'error')
        return redirect(url_for('main.index'))

@bp.route('/<barcode>')
def detail(barcode):
    """Zeigt die Details eines Werkzeugs"""
    tool = Database.query('''
        SELECT t.*, 
               l.worker_barcode as lent_to,
               l.lent_at as lending_date
        FROM tools t
        LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
        WHERE t.barcode = ? AND t.deleted = 0
    ''', [barcode], one=True)
    
    if not tool:
        flash('Werkzeug nicht gefunden', 'error')
        return redirect(url_for('tools.index'))
    
    # Hole vordefinierte Kategorien und Standorte aus den Einstellungen
    categories = Database.get_categories('tools')
    locations = Database.get_locations('tools')
    
    # Hole kombinierten Verlauf aus Ausleihen und Statusänderungen
    history = Database.query('''
        SELECT 
            'Ausleihe/Rückgabe' as action_type,
            lent_at as action_date,
            worker_barcode as worker,
            CASE 
                WHEN returned_at IS NULL THEN 'Ausgeliehen'
                ELSE 'Zurückgegeben'
            END as action,
            NULL as reason
        FROM lendings 
        WHERE tool_barcode = ?
        UNION ALL
        SELECT 
            'Statusänderung' as action_type,
            created_at as action_date,
            NULL as worker,
            new_status as action,
            reason
        FROM tool_status_changes
        WHERE tool_barcode = ?
        ORDER BY action_date DESC
    ''', [barcode, barcode])
    
    return render_template('tools/details.html',
                         tool=tool,
                         categories=[c['name'] for c in categories],
                         locations=[l['name'] for l in locations],
                         history=history)

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
        
        try:
            Database.query('''
                INSERT INTO tools 
                (name, barcode, description, category, location, status)
                VALUES (?, ?, ?, ?, ?, 'verfügbar')
            ''', [name, barcode, description, category, location])
            
            flash('Werkzeug erfolgreich hinzugefügt', 'success')
            return redirect(url_for('tools.index'))
            
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
    
    # Hole vordefinierte Kategorien und Standorte aus den Einstellungen
    categories = Database.get_categories('tools')
    locations = Database.get_locations('tools')
    
    return render_template('tools/add.html',
                         categories=[c['name'] for c in categories],
                         locations=[l['name'] for l in locations])

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

        # Status des Werkzeugs aktualisieren
        Database.query('''
            UPDATE tools 
            SET status = ?,
                modified_at = CURRENT_TIMESTAMP
            WHERE barcode = ?
        ''', [status, barcode])

        return jsonify({
            'success': True,
            'message': 'Status erfolgreich aktualisiert'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler bei der Statusänderung: {str(e)}'
        }), 500

# Weitere Tool-Routen...