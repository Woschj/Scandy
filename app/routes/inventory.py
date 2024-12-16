from flask import (
    Blueprint, 
    render_template, 
    request, 
    jsonify, 
    current_app, 
    redirect, 
    url_for, 
    flash
)
from ..models.database import Database
from ..models.tool import Tool
from ..models.worker import Worker
from ..models.consumable import Consumable
from app.utils.decorators import login_required, admin_required

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/consumables/<barcode>')
@login_required
def consumable_details(barcode):
    try:
        with Database.get_db() as conn:
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
        with Database.get_db() as conn:
            # Tool-Details abrufen
            tool = conn.execute('''
                SELECT t.*, 
                       l.lent_at,
                       l.returned_at,
                       w.firstname || ' ' || w.lastname as borrower_name
                FROM tools t
                LEFT JOIN lendings l ON t.barcode = l.tool_barcode 
                    AND l.returned_at IS NULL
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.barcode = ? AND t.deleted = 0
            ''', (barcode,)).fetchone()
            
            # Ausleihhistorie abrufen
            history = conn.execute('''
                SELECT 
                    l.lent_at,
                    l.returned_at,
                    w.firstname || ' ' || w.lastname as worker_name
                FROM lendings l
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE l.tool_barcode = ?
                ORDER BY l.lent_at DESC
            ''', (barcode,)).fetchall()
            
            if not tool:
                return "Werkzeug nicht gefunden", 404
                
            return render_template('tool_details.html', 
                                 tool=tool,
                                 history=history)
                                 
    except Exception as e:
        print(f"Fehler in tool_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/workers/<barcode>')
@login_required
def worker_details(barcode):
    try:
        with Database.get_db() as conn:
            # Worker-Details abrufen
            worker = conn.execute('''
                SELECT w.*, 
                       COUNT(CASE WHEN l.returned_at IS NULL THEN 1 END) as active_lendings
                FROM workers w
                LEFT JOIN lendings l ON w.barcode = l.worker_barcode
                WHERE w.barcode = ? AND w.deleted = 0
                GROUP BY w.id
            ''', (barcode,)).fetchone()
            
            # Aktuelle Ausleihen
            current_lendings = conn.execute('''
                SELECT t.*, l.lent_at
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                WHERE l.worker_barcode = ? 
                AND l.returned_at IS NULL
                ORDER BY l.lent_at DESC
            ''', (barcode,)).fetchall()
            
            # Ausleihhistorie
            lending_history = conn.execute('''
                SELECT t.name as tool_name,
                       l.lent_at,
                       l.returned_at,
                       t.barcode as tool_barcode
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                WHERE l.worker_barcode = ?
                AND l.returned_at IS NOT NULL
                ORDER BY l.lent_at DESC
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
    tools = Database.query('''
        SELECT t.*, 
               l.worker_barcode,
               l.lent_at,
               l.returned_at,
               w.firstname || ' ' || w.lastname as borrower_name
        FROM tools t
        LEFT JOIN (
            SELECT l1.*
            FROM lendings l1
            LEFT JOIN lendings l2 ON l1.tool_barcode = l2.tool_barcode 
                AND l1.lent_at < l2.lent_at
            WHERE l2.tool_barcode IS NULL
        ) l ON t.barcode = l.tool_barcode
        LEFT JOIN workers w ON l.worker_barcode = w.barcode
        WHERE t.deleted = 0
        ORDER BY t.name
    ''')
    return render_template('tools.html', tools=tools)

@bp.route('/consumables')
@login_required
def consumables():
    consumables = Database.query('''
        SELECT c.*, 
               c.quantity as current_stock,
               CASE 
                   WHEN c.quantity <= c.min_quantity THEN 'low'
                   ELSE 'ok'
               END as stock_status
        FROM consumables c
        WHERE c.deleted = 0
        ORDER BY c.name
    ''')
    return render_template('consumables.html', consumables=consumables)

@bp.route('/workers')
@login_required
def workers():
    workers = Database.query('''
        SELECT w.*, 
               COUNT(CASE WHEN l.returned_at IS NULL THEN 1 END) as active_lendings
        FROM workers w
        LEFT JOIN lendings l ON w.barcode = l.worker_barcode
        WHERE w.deleted = 0
        GROUP BY w.id
        ORDER BY w.lastname, w.firstname
    ''')
    return render_template('workers.html', workers=workers)

@bp.route('/manual-lending')
@admin_required
def manual_lending():
    return render_template('inventory/manual_lending.html')

@bp.route('/tools/<barcode>/update', methods=['POST'])
@login_required
def update_tool(barcode):
    try:
        print(f"Update für Werkzeug {barcode} mit Daten:", request.form)
        
        with Database.get_db() as conn:
            data = request.form
            
            # SQL-Query mit korrekten Spaltennamen
            result = conn.execute('''
                UPDATE tools 
                SET name = ?,
                    description = ?,
                    location = ?,
                    status = ?
                WHERE barcode = ?
            ''', (
                data.get('name'),
                data.get('typ'),  # typ wird in description gespeichert
                data.get('ort'),  # ort wird in location gespeichert
                data.get('status'),
                barcode
            ))
            
            conn.commit()
            
            print(f"Anzahl aktualisierter Zeilen: {result.rowcount}")
            
            flash('Werkzeug erfolgreich aktualisiert', 'success')
            return redirect(url_for('inventory.tool_details', barcode=barcode))
            
    except Exception as e:
        print(f"Fehler beim Update des Werkzeugs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/consumables/update/<barcode>', methods=['POST'])
@login_required
def update_consumable_stock(barcode):
    try:
        data = request.form
        print(f"Empfangene Formulardaten: {dict(data)}")
        
        with Database.get_db() as conn:
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
@login_required
def update_worker(barcode):
    try:
        print("Empfangene Formulardaten:", request.form)
        
        with Database.get_db() as conn:
            # Prüfen ob der Mitarbeiter existiert
            worker = conn.execute('SELECT * FROM workers WHERE barcode = ?', (barcode,)).fetchone()
            if not worker:
                raise ValueError("Mitarbeiter nicht gefunden")
            
            # Update durchführen
            conn.execute('''
                UPDATE workers 
                SET firstname = ?,
                    lastname = ?,
                    email = ?,
                    department = ?
                WHERE barcode = ?
            ''', (
                request.form.get('firstname'),
                request.form.get('lastname'),
                request.form.get('email'),
                request.form.get('department'),
                barcode
            ))
            
            conn.commit()
            
            flash('Mitarbeiter erfolgreich aktualisiert', 'success')
            return redirect(url_for('inventory.worker_details', barcode=barcode))
            
    except Exception as e:
        print(f"Fehler beim Update des Mitarbeiters: {str(e)}")
        return jsonify({'error': str(e)}), 500