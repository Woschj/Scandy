from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models.database import Database
from app.utils.decorators import login_required, admin_required

bp = Blueprint('tools', __name__, url_prefix='/tools')

@bp.route('/', methods=['GET'])
def index():
    with Database.get_db() as conn:
        cursor = conn.cursor()
        # Status-Filter aus URL
        status = request.args.get('status')
        
        # Basis-Query
        query = """
            SELECT 
                t.barcode,
                t.name,
                t.location,
                CASE 
                    WHEN t.status = 'Defekt' THEN 'Defekt'
                    WHEN l.id IS NOT NULL THEN 'Ausgeliehen'
                    ELSE 'Verfügbar'
                END as status,
                strftime('%d.%m.%Y %H:%M', l.lent_at) as status_since,
                CASE WHEN ? THEN w.firstname || ' ' || w.lastname ELSE NULL END as current_borrower,
                CASE WHEN ? THEN w.department ELSE NULL END as borrower_department
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
        """
        
        params = [session.get('is_admin', False), session.get('is_admin', False)]
        if status:
            query += """ AND LOWER(CASE 
                        WHEN t.status = 'Defekt' THEN 'Defekt'
                        WHEN l.id IS NOT NULL THEN 'Ausgeliehen'
                        ELSE 'Verfügbar'
                    END) = LOWER(?)"""
            params.append(status)
            
        query += " ORDER BY t.name"
        
        cursor.execute(query, params)
        tools = cursor.fetchall()
        
        # Hole alle unique Orte für Filter
        cursor.execute("SELECT DISTINCT location FROM tools WHERE location IS NOT NULL AND deleted = 0")
        locations = [row[0] for row in cursor.fetchall()]
        
        return render_template('tools.html', 
                             tools=tools, 
                             orte=locations,
                             selected_status=status)

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

    return render_template('tool_details.html', 
                         tool=tool,
                         lending_history=lending_history)

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