from flask import Blueprint, jsonify, request, current_app
from ..models.worker import Worker
from ..models.tool import Tool
from ..models.database import Database
from ..utils.decorators import login_required, admin_required
import traceback

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

@bp.route('/tools/<barcode>', methods=['GET'])
def get_tool(barcode):
    try:
        with Database.get_db() as conn:
            # Debug-Log
            print(f"Suche Tool mit Barcode: {barcode}")
            
            tool = conn.execute('''
                SELECT barcode, name, description, location, status, type
                FROM tools 
                WHERE barcode = ? AND deleted = 0
            ''', (barcode,)).fetchone()
            
            if tool:
                # Debug-Log
                print(f"Tool gefunden: {tool}")
                return jsonify({
                    'barcode': tool['barcode'],
                    'name': tool['name'],
                    'description': tool['description'],
                    'location': tool['location'],
                    'status': tool['status'],
                    'type': tool['type']
                })
            else:
                # Debug-Log
                print(f"Kein Tool mit Barcode {barcode} gefunden")
                return jsonify({'error': 'Tool nicht gefunden'}), 404
                
    except Exception as e:
        # Error-Log
        print(f"Fehler beim Abrufen des Tools: {str(e)}")
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

@bp.route('/lending/process', methods=['POST'])
@admin_required
def process_lending():
    try:
        data = request.json
        
        # Validierung der Eingabedaten
        required_fields = ['item_type', 'item_barcode', 'worker_barcode']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Fehlende Pflichtfelder'}), 400
            
        with Database.get_db() as conn:
            # Prüfe ob Worker existiert
            worker = conn.execute(
                "SELECT id FROM workers WHERE barcode = ? AND deleted = 0",
                (data['worker_barcode'],)
            ).fetchone()
            
            if not worker:
                return jsonify({'success': False, 'message': 'Mitarbeiter nicht gefunden'}), 404

            if data['item_type'] == 'tool':
                # Prüfe ob Tool verfügbar
                tool = conn.execute(
                    "SELECT id, status FROM tools WHERE barcode = ? AND deleted = 0",
                    (data['item_barcode'],)
                ).fetchone()
                
                if not tool:
                    return jsonify({'success': False, 'message': 'Werkzeug nicht gefunden'}), 404
                    
                # Erstelle Ausleihe
                conn.execute("""
                    INSERT INTO lendings (tool_barcode, worker_barcode, lent_at)
                    VALUES (?, ?, datetime('now'))
                """, (data['item_barcode'], data['worker_barcode']))
                
                # Aktualisiere Tool-Status
                conn.execute("""
                    UPDATE tools 
                    SET status = 'borrowed' 
                    WHERE barcode = ?
                """, (data['item_barcode'],))

            elif data['item_type'] == 'consumable':
                amount = int(data.get('amount', 1))
                
                # Prüfe ob genug Verbrauchsmaterial verfügbar
                consumable = conn.execute("""
                    SELECT id, quantity 
                    FROM consumables 
                    WHERE barcode = ? AND deleted = 0
                """, (data['item_barcode'],)).fetchone()
                
                if not consumable:
                    return jsonify({'success': False, 'message': 'Verbrauchsmaterial nicht gefunden'}), 404
                    
                if consumable['quantity'] < amount:
                    return jsonify({'success': False, 'message': 'Nicht genügend Bestand verfügbar'}), 400
                
                # Reduziere Bestand
                conn.execute("""
                    UPDATE consumables 
                    SET quantity = quantity - ? 
                    WHERE barcode = ?
                """, (amount, data['item_barcode']))
                
                # Logge Ausgabe
                conn.execute("""
                    INSERT INTO system_logs (timestamp, level, message, details)
                    VALUES (
                        datetime('now'),
                        'INFO',
                        'Verbrauchsmaterial ausgegeben',
                        json_object(
                            'barcode', ?,
                            'worker_barcode', ?,
                            'amount', ?
                        )
                    )
                """, (data['item_barcode'], data['worker_barcode'], amount))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Fehler bei der Ausleihe-Verarbeitung: {str(e)}")
        return jsonify({'success': False, 'message': 'Interner Server-Fehler'}), 500

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