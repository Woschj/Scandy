from flask import Blueprint, jsonify
from app.models.database import get_db_connection

bp = Blueprint('api', __name__)

@bp.route('/api/check_tool/<barcode>')
def check_tool(barcode):
    try:
        with get_db_connection() as conn:
            tool = conn.execute('''
                SELECT * FROM tools 
                WHERE barcode = ?
            ''', (barcode,)).fetchone()
            
            if tool:
                return jsonify({
                    'success': True,
                    'tool': dict(tool)
                })
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 