from flask import (
    Blueprint, 
    render_template, 
    request, 
    jsonify, 
    current_app, 
    redirect, 
    url_for
)
from app.models.database import get_db_connection
from app.utils.decorators import login_required, admin_required

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/add_consumable')
@admin_required
def add_consumable():
    return render_template('add_consumable.html')

@bp.route('/add_tool')
@admin_required
def add_tool():
    return render_template('add_tool.html')

@bp.route('/add_worker')
@admin_required
def add_worker():
    return render_template('add_worker.html')

@bp.route('/consumables/<barcode>')
@login_required
def consumable_details(barcode):
    try:
        with get_db_connection() as conn:
            print(f"Aufgerufener Barcode: {barcode}")
            
            consumable = conn.execute('''
                SELECT c.* 
                FROM consumables c
                WHERE c.barcode = ? AND c.deleted = 0
            ''', (barcode,)).fetchone()
            
            print(f"Gefundene Daten: {dict(consumable) if consumable else 'Nicht gefunden'}")
            
            history = conn.execute('''
                SELECT 
                    strftime('%d.%m.%Y %H:%M', ch.timestamp) as formatted_time,
                    ch.quantity as amount,
                    ch.action,
                    w.name || ' ' || w.lastname as worker_name
                FROM consumables_history ch
                LEFT JOIN workers w ON ch.worker_barcode = w.barcode
                WHERE ch.consumable_barcode = ?
                ORDER BY ch.timestamp DESC
            ''', (barcode,)).fetchall()
            
            if not consumable:
                return "Verbrauchsmaterial nicht gefunden", 404
                
            return render_template('consumable_details.html', 
                                 consumable=consumable,
                                 history=history)
    except Exception as e:
        print(f"Fehler in consumable_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/tools/<barcode>')
@login_required
def tool_details(barcode):
    try:
        with get_db_connection() as conn:
            print(f"Aufgerufener Barcode: {barcode}")
            
            tool = conn.execute('''
                SELECT t.*, 
                       CASE 
                           WHEN l.id IS NOT NULL AND l.return_time IS NULL 
                           THEN w.name || ' ' || w.lastname 
                           ELSE NULL 
                       END as current_borrower
                FROM tools t
                LEFT JOIN lendings l ON t.barcode = l.tool_barcode 
                    AND l.return_time IS NULL
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.barcode = ? AND t.deleted = 0
            ''', (barcode,)).fetchone()
            
            print(f"Gefundene Daten: {dict(tool) if tool else 'Nicht gefunden'}")
            
            # Ausleihhistorie
            lendings = conn.execute('''
                SELECT 
                    strftime('%d.%m.%Y %H:%M', l.lending_time) as checkout_time,
                    strftime('%d.%m.%Y %H:%M', l.return_time) as return_time,
                    w.name || ' ' || w.lastname as worker_name
                FROM lendings l
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE l.tool_barcode = ?
                ORDER BY l.lending_time DESC
            ''', (barcode,)).fetchall()
            
            # Statushistorie - Angepasst an die tool_status_history Tabelle
            status_history = conn.execute('''
                SELECT 
                    strftime('%d.%m.%Y %H:%M', tsh.timestamp) as formatted_time,
                    tsh.action as new_status,
                    w.name || ' ' || w.lastname as changed_by
                FROM tool_status_history tsh
                LEFT JOIN workers w ON tsh.worker_barcode = w.barcode
                WHERE tsh.tool_barcode = ?
                ORDER BY tsh.timestamp DESC
            ''', (barcode,)).fetchall()
            
            if not tool:
                return "Werkzeug nicht gefunden", 404
                
            return render_template('tool_details.html', 
                                 tool=tool,
                                 lendings=lendings,
                                 status_history=status_history)
    except Exception as e:
        print(f"Fehler in tool_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/workers/<barcode>')
@login_required
def worker_details(barcode):
    try:
        with get_db_connection() as conn:
            print(f"Aufgerufener Barcode: {barcode}")
            
            worker = conn.execute('''
                SELECT w.*,
                       COUNT(DISTINCT CASE WHEN l.return_time IS NULL THEN l.tool_barcode END) as active_lendings
                FROM workers w
                LEFT JOIN lendings l ON w.barcode = l.worker_barcode
                WHERE w.barcode = ? AND w.deleted = 0
                GROUP BY w.id
            ''', (barcode,)).fetchone()
            
            print(f"Gefundene Daten: {dict(worker) if worker else 'Nicht gefunden'}")
            
            # Aktuelle Ausleihen
            current_lendings = conn.execute('''
                SELECT 
                    strftime('%d.%m.%Y %H:%M', l.lending_time) as formatted_checkout_time,
                    t.name as item_name,
                    t.name as item_type,
                    '1 Stück' as amount_display
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                WHERE l.worker_barcode = ? AND l.return_time IS NULL
                ORDER BY l.lending_time DESC
            ''', (barcode,)).fetchall()
            
            # Vergangene Ausleihen
            lending_history = conn.execute('''
                SELECT 
                    strftime('%d.%m.%Y %H:%M', l.lending_time) as formatted_checkout_time,
                    strftime('%d.%m.%Y %H:%M', l.return_time) as formatted_return_time,
                    t.name as item_name,
                    t.name as item_type,
                    '1 Stück' as amount_display
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                WHERE l.worker_barcode = ? AND l.return_time IS NOT NULL
                ORDER BY l.lending_time DESC
            ''', (barcode,)).fetchall()
            
            if not worker:
                return "Mitarbeiter nicht gefunden", 404
                
            return render_template('worker_details.html', 
                                 worker=worker,
                                 current_lendings=current_lendings,
                                 lending_history=lending_history)
    except Exception as e:
        print(f"Fehler in worker_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/tools')
@login_required
def tools():
    try:
        with get_db_connection() as conn:
            tools = conn.execute('''
                SELECT t.*, 
                       CASE 
                           WHEN l.id IS NOT NULL AND l.return_time IS NULL 
                           THEN w.name || ' ' || w.lastname 
                           ELSE NULL 
                       END as current_borrower
                FROM tools t
                LEFT JOIN lendings l ON t.barcode = l.tool_barcode 
                    AND l.return_time IS NULL
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.deleted = 0 
                ORDER BY t.name
            ''').fetchall()
            
            # Orte für Filter
            orte = conn.execute('''
                SELECT DISTINCT location 
                FROM tools 
                WHERE location IS NOT NULL 
                AND deleted = 0
            ''').fetchall()
            
            return render_template('tools.html', 
                                tools=tools,
                                orte=[o[0] for o in orte if o[0]])
    except Exception as e:
        current_app.logger.error(f'Datenbankfehler: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/consumables')
@login_required
def consumables():
    try:
        with get_db_connection() as conn:
            consumables = conn.execute('''
                SELECT c.*,
                       CASE 
                           WHEN c.bestand <= c.mindestbestand THEN 'Nachbestellen'
                           WHEN c.bestand = 0 THEN 'Leer'
                           ELSE 'Verfügbar'
                       END as status
                FROM consumables c
                WHERE c.deleted = 0
                ORDER BY c.bezeichnung
            ''').fetchall()
            
            # Orte und Typen für Filter
            orte = conn.execute('SELECT DISTINCT ort FROM consumables WHERE deleted = 0').fetchall()
            typen = conn.execute('SELECT DISTINCT typ FROM consumables WHERE deleted = 0').fetchall()
            
            return render_template('consumables.html', 
                                consumables=consumables,
                                orte=[o[0] for o in orte if o[0]],
                                typen=[t[0] for t in typen if t[0]])
    except Exception as e:
        current_app.logger.error(f'Datenbankfehler: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/workers')
@login_required
def workers():
    try:
        with get_db_connection() as conn:
            workers = conn.execute('''
                SELECT w.*, 
                       COUNT(DISTINCT l.tool_barcode) as active_lendings
                FROM workers w
                LEFT JOIN lendings l ON w.barcode = l.worker_barcode 
                    AND l.return_time IS NULL
                WHERE w.deleted = 0
                GROUP BY w.id
                ORDER BY w.lastname, w.name
            ''').fetchall()
            
            # Bereiche für Filter (nur wenn die Spalte existiert)
            try:
                bereiche = conn.execute('''
                    SELECT DISTINCT bereich 
                    FROM workers 
                    WHERE bereich IS NOT NULL 
                    AND deleted = 0
                ''').fetchall()
            except:
                bereiche = []
            
            return render_template('workers.html', 
                                workers=workers,
                                bereiche=[b[0] for b in bereiche if b[0]])
    except Exception as e:
        current_app.logger.error(f'Datenbankfehler: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/manual-lending')
@admin_required
def manual_lending():
    return render_template('inventory/manual_lending.html')

@bp.route('/tools/update/<barcode>', methods=['POST'])
@login_required
def update_tool(barcode):
    try:
        data = request.form
        print(f"Empfangene Formulardaten: {dict(data)}")
        
        with get_db_connection() as conn:
            # Aktuelle Daten abrufen
            current_tool = conn.execute('SELECT * FROM tools WHERE barcode = ?', 
                                     (barcode,)).fetchone()
            
            # Update durchführen
            update_query = '''
                UPDATE tools 
                SET name = ?,
                    location = ?,
                    description = ?,
                    status = ?,
                    updated_at = datetime('now')
                WHERE barcode = ?
            '''
            update_values = (
                data.get('name', current_tool['name']),
                data.get('location', current_tool['location']),
                data.get('description', current_tool['description']),
                data.get('status', current_tool['status']),
                barcode
            )
            
            conn.execute(update_query, update_values)
            
            # Statusänderung in Historie eintragen mit "admin" als worker_barcode
            if data.get('status') != current_tool['status']:
                conn.execute('''
                    INSERT INTO tool_status_history 
                    (tool_barcode, action, worker_barcode, timestamp)
                    VALUES (?, ?, 'admin', datetime('now'))
                ''', (barcode, data.get('status')))
            
            conn.commit()
            
        return redirect(url_for('inventory.tools'))
        
    except Exception as e:
        print(f"Fehler beim Update: {str(e)}")
        current_app.logger.error(f'Fehler beim Aktualisieren des Werkzeugs: {str(e)}')
        return jsonify({'error': str(e)}), 500 

@bp.route('/consumables/update/<barcode>', methods=['POST'])
@login_required
def update_consumable_stock(barcode):
    try:
        data = request.form
        print(f"Empfangene Formulardaten: {dict(data)}")
        
        with get_db_connection() as conn:
            # Aktuelle Daten abrufen
            current_consumable = conn.execute('''
                SELECT * FROM consumables 
                WHERE barcode = ? AND deleted = 0
            ''', (barcode,)).fetchone()
            
            if not current_consumable:
                return "Verbrauchsmaterial nicht gefunden", 404
            
            # Update durchführen
            update_query = '''
                UPDATE consumables 
                SET bezeichnung = ?,
                    typ = ?,
                    ort = ?,
                    bestand = ?,
                    mindestbestand = ?,
                    einheit = ?
                WHERE barcode = ?
            '''
            update_values = (
                data.get('bezeichnung', current_consumable['bezeichnung']),
                data.get('typ', current_consumable['typ']),
                data.get('ort', current_consumable['ort']),
                int(data.get('bestand', current_consumable['bestand'])),
                int(data.get('mindestbestand', current_consumable['mindestbestand'])),
                data.get('einheit', current_consumable['einheit']),
                barcode
            )
            
            conn.execute(update_query, update_values)
            
            # Bestandsänderung in Historie eintragen
            if int(data.get('bestand')) != current_consumable['bestand']:
                conn.execute('''
                    INSERT INTO consumables_history 
                    (consumable_barcode, action, worker_barcode, quantity, timestamp)
                    VALUES (?, ?, 'admin', ?, datetime('now'))
                ''', (barcode, 'Bestandsänderung', int(data.get('bestand'))))
            
            conn.commit()
            
        return redirect(url_for('inventory.consumables'))
        
    except Exception as e:
        print(f"Fehler beim Update des Verbrauchsmaterials: {str(e)}")
        return jsonify({'error': str(e)}), 500 

@bp.route('/workers/update/<barcode>', methods=['POST'])
@admin_required
def update_worker(barcode):
    try:
        data = request.form
        print(f"Empfangene Formulardaten: {dict(data)}")
        
        with get_db_connection() as conn:
            # Aktuelle Daten abrufen
            current_worker = conn.execute('''
                SELECT * FROM workers 
                WHERE barcode = ? AND deleted = 0
            ''', (barcode,)).fetchone()
            
            if not current_worker:
                return "Mitarbeiter nicht gefunden", 404
            
            # Update durchführen
            conn.execute('''
                UPDATE workers 
                SET name = ?,
                    lastname = ?
                WHERE barcode = ?
            ''', (
                data.get('name', current_worker['name']),
                data.get('lastname', current_worker['lastname']),
                barcode
            ))
            
            conn.commit()
            
        return redirect(url_for('inventory.workers'))
        
    except Exception as e:
        print(f"Fehler beim Update des Mitarbeiters: {str(e)}")
        return jsonify({'error': str(e)}), 500