from flask import Blueprint, render_template, flash, redirect, url_for
from app.models.database import get_db_connection
from app.utils.decorators import login_required

bp = Blueprint('history', __name__)

@bp.route('/history')
@login_required
def view_history():
    try:
        with get_db_connection() as conn:
            history = conn.execute('''
                SELECT l.*, w.name, w.lastname,
                    t.name as tool_name,
                    t.description as tool_description,
                    c.bezeichnung as consumable_name,
                    c.typ as consumable_type
                FROM lendings l
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                LEFT JOIN tools t ON l.tool_barcode = t.barcode
                LEFT JOIN consumables c ON l.tool_barcode = c.barcode
                ORDER BY l.lending_time DESC
            ''').fetchall()
            
        return render_template('history.html', history=history)
    except Exception as e:
        flash('Fehler beim Laden der Historie', 'error')
        return redirect(url_for('index')) 