from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.database import Database
from app.models.worker import Worker
from app.utils.decorators import login_required, admin_required
from datetime import datetime

bp = Blueprint('workers', __name__, url_prefix='/workers')

@bp.route('/')
@admin_required
def index():
    """Mitarbeiter-Übersicht"""
    try:
        workers = Database.query('''
            SELECT w.*,
                   COUNT(DISTINCT l.id) as active_lendings
            FROM workers w
            LEFT JOIN lendings l ON w.barcode = l.worker_barcode AND l.returned_at IS NULL
            WHERE w.deleted = 0
            GROUP BY w.barcode
            ORDER BY w.lastname, w.firstname
        ''')
        
        # Hole Filter-Optionen
        departments = Database.query('''
            SELECT DISTINCT department FROM workers 
            WHERE deleted = 0 AND department IS NOT NULL
            ORDER BY department
        ''')
        
        # Template-Konfiguration
        config = {
            'columns': [
                {'key': 'name', 'label': 'Name'},
                {'key': 'barcode', 'label': 'Barcode'},
                {'key': 'department', 'label': 'Abteilung'},
                {'key': 'lendings', 'label': 'Ausleihen'},
                {'key': 'actions', 'label': 'Aktionen', 'align': 'right'}
            ],
            'filters': [
                {
                    'id': 'departmentFilter',
                    'placeholder': 'Alle Abteilungen',
                    'options': [{'value': d['department'], 'label': d['department']} for d in departments]
                },
                {
                    'id': 'lendingFilter',
                    'placeholder': 'Ausleihstatus',
                    'options': [
                        {'value': 'with_lendings', 'label': 'Mit Ausleihen'},
                        {'value': 'without_lendings', 'label': 'Ohne Ausleihen'}
                    ]
                }
            ],
            'items': [{
                'name': f'<a href="{url_for("workers.details", barcode=item["barcode"])}" class="link link-hover font-medium">{item["lastname"]}, {item["firstname"]}</a>',
                'barcode': f'<code>{item["barcode"]}</code>',
                'department': item['department'],
                'lendings': f'''
                    <span class="badge {
                        'badge-warning' if item['active_lendings'] > 0 else 'badge-success'
                    } gap-1">
                        <i class="fas fa-tools"></i>
                        {item['active_lendings']} aktiv
                    </span>
                ''',
                'actions': f'''
                    <div class="btn-group">
                        <button class="btn btn-sm" onclick="editWorker('{item['barcode']}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-error" onclick="deleteWorker('{item['barcode']}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                ''',
                'data_attrs': {
                    'department': item['department'],
                    'lending': 'with_lendings' if item['active_lendings'] > 0 else 'without_lendings'
                }
            } for item in workers],
            'add_url': url_for('workers.add'),
            'add_text': 'Neuer Mitarbeiter'
        }
        
        return render_template('shared/list_view.html', **config)
        
    except Exception as e:
        flash(f'Fehler beim Laden der Mitarbeiter: {str(e)}', 'error')
        return redirect(url_for('index'))

@bp.route('/workers/add', methods=['GET', 'POST'])
@admin_required
def add():
    departments = [
        'Medien und Digitales',
        'Technik',
        'Kaufmännisches',
        'Service',
        'APE',
        'Mitarbeiter'
    ]
    
    if request.method == 'POST':
        barcode = request.form['barcode']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        department = request.form.get('department', '')
        email = request.form.get('email', '')
        
        if department not in departments:
            flash('Ungültige Abteilung ausgewählt', 'error')
            return render_template('admin/add_worker.html', departments=departments)
        
        try:
            Database.query(
                '''INSERT INTO workers 
                   (barcode, firstname, lastname, department, email) 
                   VALUES (?, ?, ?, ?, ?)''',
                [barcode, firstname, lastname, department, email]
            )
            flash('Mitarbeiter erfolgreich hinzugefügt', 'success')
            return redirect(url_for('workers.index'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
            
    return render_template('admin/add_worker.html', departments=departments)

@bp.route('/<barcode>')
@login_required
def details(barcode):
    departments = [
        'Medien und Digitales',
        'Technik',
        'Kaufmännisches',
        'Service',
        'APE',
        'Mitarbeiter'
    ]
    
    worker = Database.query('SELECT * FROM workers WHERE barcode = ? AND deleted = 0', [barcode], one=True)
    if not worker:
        flash('Mitarbeiter nicht gefunden', 'error')
        return redirect(url_for('workers.index'))

    # Hole aktuelle Ausleihen
    current_lendings = Database.query('''
        SELECT 
            t.name as tool_name,
            t.barcode as tool_barcode,
            strftime('%d.%m.%Y %H:%M', l.lent_at) as lent_at,
            'Werkzeug' as item_type,
            1 as amount_display
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ? 
        AND l.returned_at IS NULL
        ORDER BY l.lent_at DESC
    ''', [barcode])

    # Hole Ausleihhistorie
    lending_history = Database.query('''
        SELECT 
            t.name as tool_name,
            t.barcode as tool_barcode,
            strftime('%d.%m.%Y %H:%M', l.lent_at) as lent_at,
            strftime('%d.%m.%Y %H:%M', l.returned_at) as returned_at,
            'Werkzeug' as item_type,
            NULL as amount_display
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ?
        AND l.returned_at IS NOT NULL
        UNION ALL
        SELECT 
            c.name as tool_name,
            c.barcode as tool_barcode,
            strftime('%d.%m.%Y %H:%M', cu.used_at) as lent_at,
            strftime('%d.%m.%Y %H:%M', cu.used_at) as returned_at,
            'Verbrauchsmaterial' as item_type,
            NULL as amount_display
        FROM consumable_usage cu
        JOIN consumables c ON cu.consumable_id = c.id
        JOIN workers w ON cu.worker_id = w.id
        WHERE w.barcode = ?
        ORDER BY lent_at DESC
    ''', [barcode, barcode])

    return render_template('worker_details.html', 
                         worker=worker,
                         current_lendings=current_lendings,
                         lending_history=lending_history,
                         departments=departments)

@bp.route('/<barcode>/edit', methods=['POST'])
@admin_required
def edit(barcode):
    try:
        Database.query('''
            UPDATE workers 
            SET firstname = ?,
                lastname = ?,
                email = ?,
                department = ?
            WHERE barcode = ?
        ''', [
            request.form['firstname'],
            request.form['lastname'],
            request.form.get('email', ''),
            request.form.get('department', ''),
            barcode
        ])
        flash('Mitarbeiter erfolgreich aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    
    return redirect(url_for('workers.details', barcode=barcode))

@bp.route('/<barcode>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete(barcode):
    try:
        print(f"Lösche Mitarbeiter: {barcode}")
        result = Database.soft_delete('workers', barcode)
        print(f"Lösch-Ergebnis: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Fehler beim Löschen: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        })

@bp.route('/workers/search')
def search():
    query = request.args.get('q', '')
    try:
        workers = Database.query('''
            SELECT * FROM workers 
            WHERE (firstname LIKE ? OR lastname LIKE ? OR barcode LIKE ?) 
            AND deleted = 0
        ''', [f'%{query}%', f'%{query}%', f'%{query}%'])
        return jsonify([dict(worker) for worker in workers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500