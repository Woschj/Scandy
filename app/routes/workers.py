from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from app.models.database import get_db_connection
from app.utils.decorators import login_required, admin_required
from app.models.worker import Worker

bp = Blueprint('workers', __name__, url_prefix='/workers')

@bp.route('/')
@login_required
def index():
    filter_type = request.args.get('filter')
    workers = Worker.get_all_active()
    if filter_type == 'with_tools':
        workers = [w for w in workers if Worker.has_active_lendings(w['barcode'])]
    return render_template('workers.html', workers=workers)

@bp.route('/<barcode>')
@login_required
def details(barcode):
    try:
        with get_db_connection() as conn:
            worker = conn.execute('''
                SELECT w.*, 
                       COUNT(CASE WHEN l.return_time IS NULL THEN 1 END) as active_lendings
                FROM workers w
                LEFT JOIN lendings l ON w.barcode = l.worker_barcode
                WHERE w.barcode = ? AND w.deleted = 0
                GROUP BY w.id
            ''', (barcode,)).fetchone()
            
            if not worker:
                flash('Mitarbeiter nicht gefunden.', 'error')
                return redirect(url_for('workers.index'))
            
            # Aktuelle Ausleihen
            active_lendings = conn.execute('''
                SELECT l.*, t.name as tool_name
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                WHERE l.worker_barcode = ? AND l.return_time IS NULL
                ORDER BY l.lending_time DESC
            ''', (barcode,)).fetchall()
            
            # Ausleihhistorie
            lending_history = conn.execute('''
                SELECT l.*, t.name as tool_name
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                WHERE l.worker_barcode = ? AND l.return_time IS NOT NULL
                ORDER BY l.return_time DESC
            ''', (barcode,)).fetchall()
            
            return render_template('worker_details.html',
                                worker=worker,
                                active_lendings=active_lendings,
                                lending_history=lending_history)
    except Exception as e:
        current_app.logger.error(f'Fehler in worker_details: {str(e)}')
        return str(e), 500
    
@bp.route('/edit/<barcode>', methods=['GET', 'POST'])
@login_required
def edit(barcode):
    if request.method == 'POST':
        name = request.form.get('name')
        lastname = request.form.get('lastname')
        bereich = request.form.get('bereich')    # Diese Zeile hinzufügen
        email = request.form.get('email')        # Diese Zeile hinzufügen
        
        Worker.update(barcode, name, lastname, bereich, email)  # bereich und email hinzufügen
        return redirect(url_for('workers.details', barcode=barcode))
    
    worker = Worker.get_by_barcode(barcode)
    if worker is None:
        return redirect(url_for('workers.index'))
    return render_template('worker_details.html', worker=worker)