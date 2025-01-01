from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models.database import Database
from app.utils.decorators import admin_required
from functools import wraps

bp = Blueprint('tools', __name__, url_prefix='/tools')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            # Prüfe ob die Route öffentlich ist
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT is_public FROM access_settings WHERE route = ?', 
                             [request.endpoint])
                result = cursor.fetchone()
                if not result or not result['is_public']:
                    flash('Diese Seite erfordert eine Anmeldung.', 'warning')
                    return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_tools():
    """Holt alle aktiven Werkzeuge aus der Datenbank"""
    with Database.get_db() as conn:
        cursor = conn.cursor()
        
        # Optimierte Query mit allen benötigten Informationen
        query = """
            SELECT t.*, 
                   l.lent_at,
                   w.firstname || ' ' || w.lastname as lent_to
            FROM tools t
            LEFT JOIN (
                SELECT tool_barcode, MAX(id) as latest_id
                FROM lendings 
                WHERE returned_at IS NULL
                GROUP BY tool_barcode
            ) latest ON t.barcode = latest.tool_barcode
            LEFT JOIN lendings l ON latest.latest_id = l.id
            LEFT JOIN workers w ON l.worker_barcode = w.barcode
            WHERE t.deleted = 0
            ORDER BY t.name
        """
        
        tools = cursor.execute(query).fetchall()
        return tools

@bp.route('/')
def index():
    """Öffentliche Werkzeug-Übersicht"""
    try:
        tools = get_tools()
        
        # Hole Filter-Optionen
        categories = Database.query('''
            SELECT DISTINCT category FROM tools 
            WHERE deleted = 0 AND category IS NOT NULL
            ORDER BY category
        ''')
        
        locations = Database.query('''
            SELECT DISTINCT location FROM tools 
            WHERE deleted = 0 AND location IS NOT NULL
            ORDER BY location
        ''')
        
        return render_template('tools/index.html',
                             tools=tools,
                             categories=[c['category'] for c in categories],
                             locations=[l['location'] for l in locations])
        
    except Exception as e:
        flash(f'Fehler beim Laden der Werkzeuge: {str(e)}', 'error')
        return redirect(url_for('tools.index'))

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    """Werkzeug hinzufügen (nur Admin)"""
    if request.method == 'POST':
        try:
            Database.query('''
                INSERT INTO tools (barcode, name, description, location, status, category, created_at, deleted)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
            ''', [
                request.form.get('barcode'),
                request.form.get('name'),
                request.form.get('description'),
                request.form.get('location'),
                'Verfügbar',  # Standardstatus
                request.form.get('category')
            ])
            flash('Werkzeug erfolgreich hinzugefügt', 'success')
            return redirect(url_for('tools.index'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
    
    return render_template('admin/add_tool.html')

@bp.route('/<barcode>', methods=['GET'])
@login_required
def details(barcode):
    """Werkzeug-Details (Login erforderlich)"""
    tool = Database.query('''
        SELECT * FROM tools 
        WHERE barcode = ? AND deleted = 0
    ''', [barcode], one=True)
    
    if not tool:
        flash('Werkzeug nicht gefunden', 'error')
        return redirect(url_for('tools.index'))

    # Hole Ausleihverlauf
    lending_history = Database.query('''
        SELECT 
            l.id,
            w.firstname || ' ' || w.lastname as worker_name,
            strftime('%d.%m.%Y %H:%M', l.lent_at) as timestamp,
            CASE 
                WHEN l.returned_at IS NULL THEN 'Ausgeliehen'
                ELSE 'Zurückgegeben'
            END as action
        FROM lendings l
        LEFT JOIN workers w ON l.worker_barcode = w.barcode
        WHERE l.tool_barcode = ?
        ORDER BY l.lent_at DESC
    ''', [barcode])

    if request.headers.get('HX-Request'):
        # Wenn HTMX Request, nur Modalinhalt zurückgeben
        return render_template('tools/details_modal.html', tool=tool)
    # Ansonsten normale Seite zurückgeben
    return render_template('tools/details.html', tool=tool)

@bp.route('/<barcode>/edit', methods=['POST'])
@admin_required
def edit(barcode):
    try:
        Database.query('''
            UPDATE tools 
            SET name = ?,
                description = ?,
                location = ?,
                status = ?,
                category = ?
            WHERE barcode = ?
            AND deleted = 0
        ''', [
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('location'),
            request.form.get('status'),
            request.form.get('category'),
            barcode
        ])
        flash('Werkzeug erfolgreich aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return redirect(url_for('tools.details', barcode=barcode))

@bp.route('/<barcode>/return', methods=['POST'])
@admin_required
def return_tool(barcode):
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            
            # Aktualisiere den Status des Werkzeugs
            cursor.execute('''
                UPDATE tools 
                SET status = 'Verfügbar'
                WHERE barcode = ?
            ''', [barcode])
            
            # Setze returned_at für die aktuelle Ausleihe
            cursor.execute('''
                UPDATE lendings 
                SET returned_at = datetime('now')
                WHERE tool_barcode = ? 
                AND returned_at IS NULL
            ''', [barcode])
            
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/<barcode>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete(barcode):
    try:
        print(f"Lösche Werkzeug: {barcode}")
        result = Database.soft_delete('tools', barcode)
        print(f"Lösch-Ergebnis: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Fehler beim Löschen: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        })

@bp.route('/manual_lending', methods=['POST'])
@login_required
def manual_lending():
    """Manuelle Ausleihe eines Werkzeugs"""
    try:
        tool_barcode = request.form.get('tool_barcode')
        worker_barcode = request.form.get('worker_barcode')
        
        print(f"Manuelle Ausleihe - Tool: {tool_barcode}, Worker: {worker_barcode}")  # Debug
        
        # Prüfe ob Tool existiert und nicht gelöscht ist
        tool = Database.query('''
            SELECT * FROM tools 
            WHERE barcode = ? AND deleted = 0
        ''', [tool_barcode], one=True)
        
        if not tool:
            return jsonify({
                'success': False,
                'message': 'Werkzeug nicht gefunden'
            })
            
        # Prüfe ob Worker existiert und nicht gelöscht ist
        worker = Database.query('''
            SELECT * FROM workers 
            WHERE barcode = ? AND deleted = 0
        ''', [worker_barcode], one=True)
        
        if not worker:
            return jsonify({
                'success': False,
                'message': 'Mitarbeiter nicht gefunden'
            })
            
        # Prüfe ob Tool bereits ausgeliehen ist
        lending = Database.query('''
            SELECT * FROM lendings 
            WHERE tool_barcode = ? AND returned_at IS NULL
        ''', [tool_barcode], one=True)
        
        if lending:
            return jsonify({
                'success': False,
                'message': 'Werkzeug ist bereits ausgeliehen'
            })
            
        # Neue Ausleihe eintragen
        Database.query('''
            INSERT INTO lendings (tool_barcode, worker_barcode, lent_at)
            VALUES (?, ?, datetime('now'))
        ''', [tool_barcode, worker_barcode])
        
        return jsonify({
            'success': True,
            'message': 'Ausleihe erfolgreich eingetragen'
        })
        
    except Exception as e:
        print(f"Fehler bei manueller Ausleihe: {str(e)}")  # Debug
        return jsonify({
            'success': False,
            'message': f'Fehler bei der Ausleihe: {str(e)}'
        })