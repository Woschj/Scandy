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