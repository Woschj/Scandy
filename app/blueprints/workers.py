@bp.route('/')
@login_required
def index():
    workers = Database.query('''
        SELECT w.*
        FROM workers w
        WHERE w.deleted = 0
        ORDER BY w.firstname, w.lastname
    ''')
    
    departments = Database.query('''
        SELECT value as name
        FROM settings 
        WHERE key LIKE 'department_%'
        ORDER BY value
    ''')
    
    return render_template('workers/index.html', 
                         workers=workers,
                         departments=departments)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        barcode = request.form.get('barcode')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        department = request.form.get('department')
        email = request.form.get('email')
        
        # Validierung...
        
        # Prüfen ob die Abteilung existiert
        if department:
            dept_exists = Database.query('''
                SELECT 1 
                FROM settings 
                WHERE key LIKE 'department_%'
                AND value = ?
            ''', [department], one=True)
            
            if not dept_exists:
                flash('Die gewählte Abteilung existiert nicht', 'error')
                return redirect(url_for('workers.add'))
        
        Database.execute('''
            INSERT INTO workers (barcode, firstname, lastname, department, email)
            VALUES (?, ?, ?, ?, ?)
        ''', [barcode, firstname, lastname, department, email])
        
        flash('Mitarbeiter wurde hinzugefügt', 'success')
        return redirect(url_for('workers.index'))
    
    # Abteilungen aus settings laden
    departments = Database.query('''
        SELECT value as name
        FROM settings 
        WHERE key LIKE 'department_%'
        ORDER BY value
    ''')
    
    return render_template('workers/add.html', departments=departments)

@bp.route('/<barcode>', methods=['GET', 'POST'])
@login_required
def detail(barcode):
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        department = request.form.get('department')
        email = request.form.get('email')
        
        # Validierung...
        
        # Prüfen ob die Abteilung existiert
        if department:
            dept_exists = Database.query('''
                SELECT 1 
                FROM settings 
                WHERE key LIKE 'department_%'
                AND value = ?
            ''', [department], one=True)
            
            if not dept_exists:
                return jsonify({
                    'success': False,
                    'message': 'Die gewählte Abteilung existiert nicht'
                }), 400
        
        Database.execute('''
            UPDATE workers 
            SET firstname = ?,
                lastname = ?,
                department = ?,
                email = ?,
                modified_at = datetime('now'),
                sync_status = 'pending'
            WHERE barcode = ?
        ''', [firstname, lastname, department, email, barcode])
        
        return jsonify({
            'success': True,
            'message': 'Mitarbeiter wurde aktualisiert'
        })
    
    worker = Database.query('''
        SELECT w.*
        FROM workers w
        WHERE w.barcode = ?
        AND w.deleted = 0
    ''', [barcode], one=True)
    
    if not worker:
        flash('Mitarbeiter nicht gefunden', 'error')
        return redirect(url_for('workers.index'))
    
    # Aktuelle Ausleihen laden
    current_lendings = Database.query('''
        SELECT l.*, t.name as tool_name
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ?
        AND l.returned_at IS NULL
        ORDER BY l.lent_at DESC
    ''', [barcode])
    
    # Ausleihhistorie laden
    lending_history = Database.query('''
        SELECT l.*, t.name as tool_name,
               CASE 
                   WHEN l.returned_at IS NULL THEN 'Ausgeliehen'
                   ELSE 'Zurückgegeben'
               END as status
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        WHERE l.worker_barcode = ?
        ORDER BY l.lent_at DESC
        LIMIT 50
    ''', [barcode])
    
    # Verbrauchsmaterial-Historie laden
    usage_history = Database.query('''
        SELECT cu.*, c.name as consumable_name
        FROM consumable_usages cu
        JOIN consumables c ON cu.consumable_barcode = c.barcode
        WHERE cu.worker_barcode = ?
        ORDER BY cu.used_at DESC
        LIMIT 50
    ''', [barcode])
    
    # Abteilungen aus settings laden
    departments = Database.query('''
        SELECT value as name
        FROM settings 
        WHERE key LIKE 'department_%'
        ORDER BY value
    ''')
    
    return render_template('workers/details.html',
                         worker=worker,
                         departments=departments,
                         current_lendings=current_lendings,
                         lending_history=lending_history,
                         usage_history=usage_history) 