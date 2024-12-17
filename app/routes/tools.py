from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.database import Database
from app.utils.decorators import admin_required

bp = Blueprint('tools', __name__, url_prefix='/inventory/tools')

@bp.route('/', methods=['GET'])
def index():
    tools = Database.query('''
        SELECT * FROM tools 
        WHERE deleted = 0 
        ORDER BY name
    ''')
    return render_template('tools.html', tools=tools)

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
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
def details(barcode):
    tool = Database.query('''
        SELECT * FROM tools 
        WHERE barcode = ? AND deleted = 0
    ''', [barcode], one=True)
    
    if not tool:
        flash('Werkzeug nicht gefunden', 'error')
        return redirect(url_for('tools.index'))

    # Ausleihverlauf abrufen
    lendings = Database.query('''
        SELECT 
            l.*,
            w.firstname || ' ' || w.lastname as worker_name,
            datetime(l.lent_at, 'localtime') as checkout_time,
            datetime(l.returned_at, 'localtime') as return_time
        FROM lendings l
        LEFT JOIN workers w ON l.worker_barcode = w.barcode
        WHERE l.tool_barcode = ?
        ORDER BY l.lent_at DESC
    ''', [barcode])

    return render_template('tool_details.html', 
                         tool=tool,
                         lendings=lendings)

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