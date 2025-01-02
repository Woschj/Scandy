from flask import Blueprint, jsonify, request, current_app
from ..models.worker import Worker
from ..models.tool import Tool
from ..models.database import Database
from ..utils.decorators import login_required, admin_required
import traceback
from app.config import Config
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.before_request
def log_request_info():
    """Loggt Details über eingehende Requests"""
    print('\n=== API Request Debug Info ===')
    print(f'Endpoint: {request.endpoint}')
    print(f'Method: {request.method}')
    print(f'URL: {request.url}')
    print(f'Headers: {dict(request.headers)}')
    print(f'Data: {request.get_data(as_text=True)}')
    print('===========================\n')

@bp.route('/workers', methods=['GET'])
def get_workers():
    workers = Worker.get_all_with_lendings()
    return jsonify([{
        'id': w['id'],
        'barcode': w['barcode'],
        'name': f"{w['firstname']} {w['lastname']}",
        'department': w['department']
    } for w in workers])

@bp.route('/inventory/tools/<barcode>', methods=['GET'])
def get_tool(barcode):
    try:
        # Debug-Logging
        print(f"Suche Werkzeug mit Barcode: {barcode}")
        
        tool = Database.query('''
            SELECT 
                id,
                barcode,
                name,
                description,
                status,
                category,
                location
            FROM tools 
            WHERE barcode = ? 
            AND deleted = 0
        ''', [barcode], one=True)
        
        # Debug-Logging
        print(f"Gefundenes Werkzeug: {tool}")
        
        if not tool:
            print(f"Kein Werkzeug gefunden für Barcode: {barcode}")
            return jsonify({'error': 'Werkzeug nicht gefunden'}), 404
            
        # Konvertiere Row-Objekt in Dictionary
        tool_dict = dict(tool)
        print(f"Konvertiertes Werkzeug: {tool_dict}")
            
        return jsonify(tool_dict)
        
    except Exception as e:
        print(f"Fehler bei Werkzeugsuche: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/inventory/workers/<barcode>', methods=['GET'])
def get_worker(barcode):
    try:
        # Debug-Logging
        print(f"Suche Mitarbeiter mit Barcode: {barcode}")
        
        worker = Database.query('''
            SELECT 
                id,
                barcode,
                firstname,
                lastname,
                department,
                email
            FROM workers 
            WHERE barcode = ? 
            AND deleted = 0
        ''', [barcode], one=True)
        
        # Debug-Logging
        print(f"Gefundener Mitarbeiter: {worker}")
        
        if not worker:
            print(f"Kein Mitarbeiter gefunden für Barcode: {barcode}")
            return jsonify({'error': 'Mitarbeiter nicht gefunden'}), 404
            
        # Konvertiere Row-Objekt in Dictionary
        worker_dict = dict(worker)
        print(f"Konvertierter Mitarbeiter: {worker_dict}")
            
        return jsonify(worker_dict)
        
    except Exception as e:
        print(f"Fehler bei Mitarbeitersuche: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/settings/colors', methods=['POST'])
@admin_required
def update_colors():
    try:
        data = request.json
        print("\n=== Color Settings Debug Info ===")
        print(f"Empfangene Farbdaten: {data}")
        print(f"Request Method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Alle registrierten Routen:")
        for rule in current_app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule}")
        
        if not data:
            print("Keine JSON-Daten empfangen!")
            return jsonify({'error': 'Keine Daten empfangen'}), 400
            
        with Database.get_db() as conn:
            # Primärfarbe aktualisieren
            conn.execute('''
                INSERT OR REPLACE INTO settings (key, value) 
                VALUES (?, ?)
            ''', ('primary_color', data.get('primary_color')))
            
            # Akzentfarbe aktualisieren
            conn.execute('''
                INSERT OR REPLACE INTO settings (key, value) 
                VALUES (?, ?)
            ''', ('accent_color', data.get('accent_color')))
            
            conn.commit()
            print("Farben erfolgreich in Datenbank gespeichert")
            
        return jsonify({
            'status': 'success', 
            'message': 'Farben erfolgreich aktualisiert',
            'data': {
                'primary_color': data.get('primary_color'),
                'accent_color': data.get('accent_color')
            }
        })
        
    except Exception as e:
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'request_data': {
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'data': request.get_data(as_text=True)
            }
        }
        print("\n=== Error Debug Info ===")
        print(f"Fehler beim Speichern der Farben:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
        print("========================\n")
        
        return jsonify(error_details), 500

@bp.after_request
def after_request(response):
    """Loggt Details über ausgehende Responses"""
    print('\n=== API Response Debug Info ===')
    print(f'Status: {response.status}')
    print(f'Headers: {dict(response.headers)}')
    print(f'Data: {response.get_data(as_text=True)}')
    print('============================\n')
    return response

# Falls es hier eine alte Version der Route gibt, 
# kommentieren Sie diese aus oder löschen Sie sie

@bp.route('/lending/return', methods=['POST'])
@admin_required
def return_tool():
    try:
        data = request.json
        tool_barcode = data.get('tool_barcode')
        
        if not tool_barcode:
            return jsonify({'success': False, 'message': 'Werkzeug-Barcode fehlt'}), 400
            
        with Database.get_db() as conn:
            # Aktualisiere Ausleihe
            conn.execute("""
                UPDATE lendings 
                SET returned_at = datetime('now')
                WHERE tool_barcode = ? 
                AND returned_at IS NULL
            """, (tool_barcode,))
            
            # Setze Tool-Status zurück
            conn.execute("""
                UPDATE tools 
                SET status = 'available' 
                WHERE barcode = ?
            """, (tool_barcode,))
            
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Fehler bei der Werkzeug-Rückgabe: {str(e)}")
        return jsonify({'success': False, 'message': 'Interner Server-Fehler'}), 500

@bp.route('/tools/<barcode>/delete', methods=['POST'])
@admin_required
def delete_tool(barcode):
    db = Database()
    result = db.soft_delete_tool(barcode)
    return jsonify(result)

@bp.route('/sync', methods=['POST'])
def sync():
    """Empfange Client-Änderungen und sende Server-Änderungen"""
    if not Config.SERVER_MODE:
        return jsonify({'error': 'Not a server'}), 403
        
    try:
        # Empfange Client-Änderungen
        client_changes = request.get_json()
        
        # Wende Client-Änderungen an
        Database.apply_changes(client_changes)
        
        # Hole Server-Änderungen
        server_changes = Database.get_changes_since(
            client_changes.get('last_sync', 0)
        )
        
        return jsonify(server_changes)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/sync/auto', methods=['POST'])
@admin_required
def toggle_auto_sync():
    """Aktiviert/Deaktiviert automatische Synchronisation"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        sync_manager = current_app.extensions['sync_manager']
        
        if enabled:
            sync_manager.start_sync_scheduler()
            message = 'Automatische Synchronisation aktiviert'
        else:
            sync_manager.stop_sync_scheduler()
            message = 'Automatische Synchronisation deaktiviert'
            
        # Speichere Einstellung in der Datenbank
        Database.query('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', ['auto_sync', str(int(enabled))])
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500

@bp.route('/sync/now', methods=['POST'])
@admin_required
def trigger_sync():
    """Löst manuelle Synchronisation aus"""
    try:
        result = Database.sync_with_server()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Sync-Fehler: {str(e)}'
        }), 500

@bp.route('/sync/status')
@admin_required
def get_sync_status():
    """Gibt den aktuellen Sync-Status zurück"""
    try:
        status = Database.query('''
            SELECT last_sync, last_attempt, status, error
            FROM sync_status
            ORDER BY id DESC LIMIT 1
        ''', one=True)
        
        auto_sync = Database.query('''
            SELECT value FROM settings
            WHERE key = 'auto_sync'
        ''', one=True)
        
        return jsonify({
            'success': True,
            'last_sync': status['last_sync'] if status else None,
            'last_attempt': status['last_attempt'] if status else None,
            'status': status['status'] if status else 'never',
            'error': status['error'] if status else None,
            'auto_sync': bool(int(auto_sync['value'])) if auto_sync else False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500

@bp.route('/barcode/<code>')
def generate_barcode(code):
    """Generiert einen Barcode als Bild"""
    try:
        code128 = barcode.get('code128', code, writer=ImageWriter())
        buffer = BytesIO()
        code128.write(buffer)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        return jsonify({
            'barcode': f'data:image/png;base64,{image_base64}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/lending/process', methods=['POST'])
@admin_required
def process_lending():
    """Verarbeitet eine Ausleihe oder Rückgabe"""
    try:
        data = request.json
        item_type = data.get('type')
        item_id = data.get('item_id')
        worker_id = data.get('worker_id')
        action = data.get('action')
        
        with Database.get_db() as conn:
            if item_type == 'tool':
                if action == 'lend':
                    conn.execute(
                        '''INSERT INTO lendings 
                           (tool_id, worker_id, lent_at) 
                           VALUES (?, ?, CURRENT_TIMESTAMP)''',
                        [item_id, worker_id]
                    )
                    conn.execute(
                        'UPDATE tools SET status = "ausgeliehen" WHERE id = ?',
                        [item_id]
                    )
                else:
                    conn.execute(
                        '''UPDATE lendings 
                           SET returned_at = CURRENT_TIMESTAMP 
                           WHERE tool_id = ? AND returned_at IS NULL''',
                        [item_id]
                    )
                    conn.execute(
                        'UPDATE tools SET status = "verfügbar" WHERE id = ?',
                        [item_id]
                    )
            
            elif item_type == 'consumable':
                conn.execute(
                    '''INSERT INTO consumable_usage 
                       (consumable_id, worker_id, quantity, used_at) 
                       VALUES (?, ?, 1, CURRENT_TIMESTAMP)''',
                    [item_id, worker_id]
                )
                conn.execute(
                    'UPDATE consumables SET quantity = quantity - 1 WHERE id = ?',
                    [item_id]
                )
            
            conn.commit()
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/inventory/item/<barcode>', methods=['GET'])
@login_required
def get_item(barcode):
    try:
        # Erst in Werkzeugen suchen
        tool = Database.query('''
            SELECT t.*, 
                   COALESCE(t.status, 
                     CASE WHEN l.id IS NOT NULL THEN 'ausgeliehen' 
                     ELSE 'verfügbar' END) as status
            FROM tools t
            LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
            WHERE t.barcode = ? AND t.deleted = 0
        ''', [barcode], one=True)
        
        if tool:
            return jsonify({
                'id': tool['id'],
                'barcode': tool['barcode'],
                'name': tool['name'],
                'type': 'tool',
                'status': tool['status']
            })
        
        # Wenn nicht gefunden, in Verbrauchsmaterialien suchen
        consumable = Database.query('''
            SELECT * FROM consumables 
            WHERE barcode = ? AND deleted = 0
        ''', [barcode], one=True)
        
        if consumable:
            return jsonify({
                'id': consumable['id'],
                'barcode': consumable['barcode'],
                'name': consumable['name'],
                'type': 'consumable',
                'status': 'verfügbar' if consumable['quantity'] > 0 else 'nicht verfügbar'
            })
            
        return jsonify({'error': 'Artikel nicht gefunden'}), 404
        
    except Exception as e:
        print(f"Fehler beim Suchen des Items: {str(e)}")
        return jsonify({'error': str(e)}), 500