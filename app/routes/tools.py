from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from app.models.database import get_db_connection
from app.utils.decorators import login_required, admin_required
from app.models.tool import Tool

bp = Blueprint('tools', __name__, url_prefix='/tools')

@bp.route('/')
@login_required
def index():
    status = request.args.get('status')
    tools = Tool.get_all_active()
    if status:
        tools = [t for t in tools if t['status'] == status]
    return render_template('tools.html', tools=tools)

@bp.route('/<barcode>')
@login_required
def details(barcode):
    try:
        with get_db_connection() as conn:
            tool = conn.execute('''
                SELECT t.*, 
                       CASE 
                           WHEN l.return_time IS NULL THEN w.name || ' ' || w.lastname 
                           ELSE NULL 
                       END as current_user
                FROM tools t
                LEFT JOIN lendings l ON t.barcode = l.tool_barcode 
                    AND l.return_time IS NULL
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.barcode = ? AND t.deleted = 0
            ''', (barcode,)).fetchone()
            
            if not tool:
                flash('Werkzeug nicht gefunden.', 'error')
                return redirect(url_for('tools.index'))
            
            history = conn.execute('''
                SELECT l.*, w.name, w.lastname
                FROM lendings l
                JOIN workers w ON l.worker_barcode = w.barcode
                WHERE l.tool_barcode = ?
                ORDER BY l.lending_time DESC
            ''', (barcode,)).fetchall()
            
            return render_template('tool_details.html', 
                                tool=tool,
                                history=history)
    except Exception as e:
        current_app.logger.error(f'Fehler in tool_details: {str(e)}')
        return str(e), 500

@bp.route('/edit/<barcode>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(barcode):
    try:
        with get_db_connection() as conn:
            if request.method == 'POST':
                data = request.form
                conn.execute('''
                    UPDATE tools 
                    SET name = ?,
                        description = ?,
                        location = ?
                    WHERE barcode = ?
                ''', (data['name'], data['description'], data['location'], barcode))
                conn.commit()
                flash('Werkzeug erfolgreich aktualisiert.', 'success')
                return redirect(url_for('tools.details', barcode=barcode))
            
            tool = conn.execute('''
                SELECT * FROM tools 
                WHERE barcode = ? AND deleted = 0
            ''', (barcode,)).fetchone()
            
            if not tool:
                flash('Werkzeug nicht gefunden.', 'error')
                return redirect(url_for('tools.index'))
            
            return render_template('edit_tool.html', tool=tool)
    except Exception as e:
        current_app.logger.error(f'Fehler beim Bearbeiten: {str(e)}')
        return str(e), 500

@bp.route('/update_status', methods=['POST'])
@login_required
def update_status():
    try:
        data = request.get_json()
        tool_barcode = data.get('tool_barcode')
        worker_barcode = data.get('worker_barcode')
        action = data.get('action')
        
        with get_db_connection() as conn:
            if action == 'lend':
                conn.execute('''
                    INSERT INTO lendings (tool_barcode, worker_barcode, lending_time)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (tool_barcode, worker_barcode))
            elif action == 'return':
                conn.execute('''
                    UPDATE lendings 
                    SET return_time = CURRENT_TIMESTAMP
                    WHERE tool_barcode = ? AND return_time IS NULL
                ''', (tool_barcode,))
            
            conn.commit()
            return {'success': True}
    except Exception as e:
        current_app.logger.error(f'Fehler bei Statusänderung: {str(e)}')
        return {'success': False, 'error': str(e)} 