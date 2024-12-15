from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from app.models.database import get_db_connection, Tool, Consumable, Worker
from app.utils.decorators import admin_required, login_required
from app.models import Tool, Worker, Consumable

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@login_required
def dashboard():
    # Hole aktuelle Ausleihen mit vollständigen Informationen
    current_lendings = get_db_connection().execute('''
        SELECT l.*, 
               t.name as tool_name, 
               w.name as worker_name,
               w.lastname as worker_lastname,
               t.barcode as tool_barcode,
               w.barcode as worker_barcode
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        JOIN workers w ON l.worker_barcode = w.barcode
        WHERE l.return_time IS NULL
    ''').fetchall()
    
    # Werkzeug-Statistiken mit Status
    tools_stats = {
        'total': Tool.count_active(),
        'available': Tool.count_by_status('Verfügbar'),
        'lent': Tool.count_by_status('Ausgeliehen'),
        'maintenance': Tool.count_by_status('Wartung'),
        'broken': Tool.count_by_status('Defekt'),
        'status_colors': {
            'Verfügbar': 'text-success',
            'Ausgeliehen': 'text-warning',
            'Wartung': 'text-info',
            'Defekt': 'text-error'
        }
    }
    
    # Consumables Statistiken
    consumables_stats = {
        'total': Consumable.count_active(),
        'low_stock': Consumable.count_low_stock(),  # Unter Mindestbestand
        'out_of_stock': Consumable.count_out_of_stock()  # Bestand = 0
    }
    
    # Workers Statistiken
    workers_stats = {
        'total': Worker.count_active(),
        'with_tools': Worker.count_with_active_lendings()
    }
    
    return render_template('admin/dashboard.html', 
                         current_lendings=current_lendings,
                         tools_stats=tools_stats,
                         consumables_stats=consumables_stats,
                         workers_stats=workers_stats)

@bp.route('/export-data')
@admin_required
def export_data():
    return render_template('admin/export.html')

@bp.route('/settings')
@admin_required
def settings():
    return render_template('admin/settings.html')

@bp.route('/reports')
@admin_required
def reports():
    try:
        with get_db_connection() as conn:
            # Verschiedene Berichte generieren
            reports_data = {
                'most_borrowed': conn.execute('''
                    SELECT t.name, COUNT(*) as borrow_count
                    FROM lendings l
                    JOIN tools t ON l.tool_barcode = t.barcode
                    GROUP BY t.barcode
                    ORDER BY borrow_count DESC
                    LIMIT 5
                ''').fetchall(),
                'defect_tools': conn.execute('''
                    SELECT name, location
                    FROM tools
                    WHERE status = "Defekt" AND deleted = 0
                ''').fetchall()
            }
            
            return render_template('admin/reports.html', reports=reports_data)
            
    except Exception as e:
        flash(f'Fehler beim Generieren der Berichte: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/add-tool', methods=['GET', 'POST'])
@admin_required
def add_tool():
    if request.method == 'POST':
        current_app.logger.debug('POST-Anfrage empfangen')
        try:
            barcode = request.form.get('barcode')
            name = request.form.get('name')
            description = request.form.get('description')
            location = request.form.get('location')
            
            # Debug: Prüfen der eingehenden Daten
            current_app.logger.debug(f'Eingehende Daten: barcode={barcode}, name={name}')
            
            image_data = None
            if 'image' in request.files:
                image = request.files['image']
                if image.filename:
                    image_data = image.read()
                    current_app.logger.debug(f'Bild geladen: {len(image_data)} bytes')
            
            with get_db_connection() as conn:
                # Prüfen ob das Werkzeug bereits existiert
                existing = conn.execute('SELECT barcode FROM tools WHERE barcode = ?', (barcode,)).fetchone()
                if existing:
                    current_app.logger.warning(f'Werkzeug mit Barcode {barcode} existiert bereits')
                    return jsonify({'error': 'Werkzeug existiert bereits'}), 400
                
                # Werkzeug einfügen
                cursor = conn.execute('''
                    INSERT INTO tools (barcode, name, description, location, image)
                    VALUES (?, ?, ?, ?, ?)
                ''', (barcode, name, description, location, image_data))
                conn.commit()
                
                # Prüfen ob das Einfügen erfolgreich war
                if cursor.rowcount > 0:
                    current_app.logger.info(f'Werkzeug {barcode} erfolgreich hinzugefügt')
                    
                    # Zur Kontrolle: Das neu eingefügte Werkzeug auslesen
                    new_tool = conn.execute('SELECT * FROM tools WHERE barcode = ?', (barcode,)).fetchone()
                    current_app.logger.debug(f'Neu eingefügtes Werkzeug: {dict(new_tool)}')
                    
                    flash('Werkzeug erfolgreich hinzugefügt!', 'success')
                    return redirect(url_for('inventory.tools'))
                else:
                    current_app.logger.error('Werkzeug wurde nicht eingefügt')
                    return jsonify({'error': 'Werkzeug konnte nicht eingefügt werden'}), 500
            
        except Exception as e:
            current_app.logger.error(f'Fehler beim Hinzufügen des Werkzeugs: {str(e)}')
            return jsonify({'error': str(e)}), 400
            
    return render_template('admin/add_tool.html')

@bp.route('/add-consumable', methods=['GET', 'POST'])
@admin_required
def add_consumable():
    if request.method == 'POST':
        try:
            barcode = request.form['barcode']
            bezeichnung = request.form['bezeichnung']
            typ = request.form['typ']
            ort = request.form['ort']
            mindestbestand = request.form['mindestbestand']
            aktueller_bestand = request.form['aktueller_bestand']
            einheit = request.form['einheit']
            image_data = request.form.get('processed_image')
            
            with get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO consumables (barcode, bezeichnung, typ, ort, 
                                          mindestbestand, aktueller_bestand, 
                                          einheit, bild)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (barcode, bezeichnung, typ, ort, mindestbestand,
                     aktueller_bestand, einheit, image_data))
                conn.commit()
                
            flash('Verbrauchsmaterial erfolgreich hinzugefügt!', 'success')
            return redirect(url_for('inventory.consumables'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen des Verbrauchsmaterials: {str(e)}', 'error')
            
    return render_template('admin/add_consumable.html')

@bp.route('/add-worker', methods=['GET', 'POST'])
@admin_required
def add_worker():
    if request.method == 'POST':
        try:
            with get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO workers (barcode, first_name, last_name, department, email)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    request.form['barcode'],
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['department'],
                    request.form['email']
                ))
                conn.commit()
                flash('Mitarbeiter erfolgreich hinzugefügt!', 'success')
                return redirect(url_for('inventory.workers'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen des Mitarbeiters: {str(e)}', 'error')
    return render_template('admin/add_worker.html')

@bp.route('/trash')
@admin_required
def trash():
    try:
        with get_db_connection() as conn:
            # Hole gelöschte Einträge aus der Datenbank
            deleted_tools = conn.execute('''
                SELECT * FROM tools 
                WHERE deleted = 1
            ''').fetchall()
            
            deleted_consumables = conn.execute('''
                SELECT * FROM consumables 
                WHERE deleted = 1
            ''').fetchall()
            
            deleted_workers = conn.execute('''
                SELECT * FROM workers 
                WHERE deleted = 1
            ''').fetchall()
            
            return render_template('admin/trash.html',
                                deleted_tools=deleted_tools,
                                deleted_consumables=deleted_consumables,
                                deleted_workers=deleted_workers)
    except Exception as e:
        flash(f'Fehler beim Laden der gelöschten Einträge: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/restore/<type>/<barcode>', methods=['POST'])
@admin_required
def restore_item(type, barcode):
    try:
        with get_db_connection() as conn:
            if type == 'tool':
                table = 'tools'
            elif type == 'consumable':
                table = 'consumables'
            elif type == 'worker':
                table = 'workers'
            else:
                return jsonify({'success': False, 'message': 'Ungültiger Typ'})
            
            conn.execute(f'''
                UPDATE {table}
                SET deleted = 0
                WHERE barcode = ?
            ''', (barcode,))
            conn.commit()
            
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/system-logs')
@admin_required
def system_logs():
    try:
        with get_db_connection() as conn:
            logs = conn.execute('''
                SELECT timestamp, level, message
                FROM system_logs
                ORDER BY timestamp DESC
                LIMIT 100
            ''').fetchall()
            return render_template('admin/system_logs.html', logs=logs)
    except Exception as e:
        flash(f'Fehler beim Laden der Systemlogs: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/manual_lending')
@login_required
@admin_required
def manual_lending():
    print("=== MANUAL LENDING PAGE LOADED ===")
    with get_db_connection() as conn:
        print("Loading active lendings...")
        # Hole aktive Werkzeug-Ausleihen
        tool_lendings = conn.execute('''
            SELECT 
                l.lending_time,
                t.name as item_name,
                t.barcode as item_barcode,
                w.name as worker_name,
                w.lastname as worker_lastname,
                'tool' as item_type,
                NULL as amount,
                NULL as einheit
            FROM lendings l
            JOIN tools t ON l.tool_barcode = t.barcode
            JOIN workers w ON l.worker_barcode = w.barcode
            WHERE l.return_time IS NULL
        ''').fetchall()

        # Hole aktive Verbrauchsmaterial-Ausgaben
        consumable_lendings = conn.execute('''
            SELECT 
                cl.lending_time,
                c.bezeichnung as item_name,
                c.barcode as item_barcode,
                w.name as worker_name,
                w.lastname as worker_lastname,
                'consumable' as item_type,
                cl.quantity as amount,
                c.einheit
            FROM consumable_lendings cl
            JOIN consumables c ON cl.consumable_barcode = c.barcode
            JOIN workers w ON cl.worker_barcode = w.barcode
            WHERE cl.return_time IS NULL
            AND cl.lending_time >= datetime('now', '-1 day')
            ORDER BY cl.lending_time DESC
        ''').fetchall()

        print(f"Found {len(tool_lendings)} active tool lendings")
        print(f"Found {len(consumable_lendings)} active consumable lendings")

        # Kombiniere beide Listen und konvertiere zu Dict
        active_lendings = []
        for lending in tool_lendings + consumable_lendings:
            active_lendings.append({
                'item_name': lending['item_name'],
                'item_barcode': lending['item_barcode'],
                'worker_name': f"{lending['worker_name']} {lending['worker_lastname']}",
                'formatted_time': lending['lending_time'],
                'item_type': lending['item_type'],
                'amount': lending['amount'],
                'einheit': lending['einheit']
            })

        # Hole verfügbare Werkzeuge und Verbrauchsmaterialien und konvertiere zu Dict
        tools = [dict(row) for row in conn.execute('''
            SELECT barcode, name as bezeichnung 
            FROM tools 
            WHERE deleted = 0 AND status = 'Verfügbar'
        ''').fetchall()]

        consumables = [dict(row) for row in conn.execute('''
            SELECT barcode, bezeichnung 
            FROM consumables 
            WHERE deleted = 0 AND bestand > 0
        ''').fetchall()]

        workers = [dict(row) for row in conn.execute(
            'SELECT * FROM workers WHERE deleted = 0'
        ).fetchall()]

        return render_template('admin/manual_lending.html',
                             tools=tools,
                             consumables=consumables,
                             workers=workers,
                             active_lendings=active_lendings)

@bp.route('/process_lending', methods=['POST'])
@login_required
@admin_required
def process_lending():
    print("=== PROCESS LENDING STARTED ===")
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        worker_barcode = data.get('worker_barcode')
        item_type = data.get('item_type')
        item_barcode = data.get('item_barcode')
        amount = int(data.get('amount', 1))
        
        print(f"Processing: Type={item_type}, Item={item_barcode}, Worker={worker_barcode}, Amount={amount}")

        if item_type == 'consumable':
            print("Processing consumable lending...")
            with get_db_connection() as conn:
                consumable = conn.execute('''
                    SELECT bestand, bezeichnung FROM consumables 
                    WHERE barcode = ? AND deleted = 0
                ''', (item_barcode,)).fetchone()
                print(f"Found consumable: {dict(consumable) if consumable else 'None'}")
                
                if not consumable or consumable['bestand'] < amount:
                    return jsonify({'error': 'Nicht genügend Bestand verfügbar'}), 400

                # Bestand aktualisieren
                conn.execute('''
                    UPDATE consumables 
                    SET bestand = bestand - ? 
                    WHERE barcode = ?
                ''', (amount, item_barcode))

                # Verleihdaten speichern
                conn.execute('''
                    INSERT INTO consumable_lendings 
                    (consumable_barcode, worker_barcode, quantity, lending_time)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (item_barcode, worker_barcode, amount))
                
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': f'{amount} {consumable["bezeichnung"]} erfolgreich ausgegeben'
                })

        elif item_type == 'tool':
            print("Processing tool lending...")
            with get_db_connection() as conn:
                # Prüfe ob Werkzeug verfügbar
                tool = conn.execute('''
                    SELECT status, name 
                    FROM tools 
                    WHERE barcode = ? AND deleted = 0
                ''', (item_barcode,)).fetchone()

                if not tool or tool['status'] != 'Verfügbar':
                    return jsonify({'error': 'Werkzeug nicht verfügbar'}), 400

                # Erstelle Ausleihe
                conn.execute('''
                    INSERT INTO lendings (tool_barcode, worker_barcode, lending_time)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (item_barcode, worker_barcode))

                # Aktualisiere Werkzeug-Status
                conn.execute('''
                    UPDATE tools 
                    SET status = 'Ausgeliehen' 
                    WHERE barcode = ?
                ''', (item_barcode,))

                conn.commit()
                return jsonify({
                    'success': True,
                    'message': f'{tool["name"]} erfolgreich ausgeliehen'
                })

    except Exception as e:
        print(f"Error in process_lending: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/process_return', methods=['POST'])
@login_required
@admin_required
def process_return():
    print("=== PROCESS RETURN STARTED ===")
    try:
        data = request.get_json()
        print(f"Received return data: {data}")
        item_barcode = data.get('item_barcode')
        item_type = data.get('item_type')

        print(f"Processing return: Type={item_type}, Item={item_barcode}")

        with get_db_connection() as conn:
            if item_type == 'tool':
                print("Processing tool return...")
                # Werkzeug zurückgeben
                conn.execute('''
                    UPDATE lendings 
                    SET return_time = CURRENT_TIMESTAMP 
                    WHERE tool_barcode = ? AND return_time IS NULL
                ''', (item_barcode,))

                # Status des Werkzeugs aktualisieren
                conn.execute('''
                    UPDATE tools 
                    SET status = 'Verfügbar' 
                    WHERE barcode = ?
                ''', (item_barcode,))

                # Logging
                conn.execute('''
                    INSERT INTO system_logs 
                    (timestamp, level, message, action, related_barcode)
                    VALUES (CURRENT_TIMESTAMP, 'INFO', ?, 'TOOL_RETURN', ?)
                ''', (f'Werkzeug zurückgegeben: {item_barcode}', item_barcode))

            elif item_type == 'consumable':
                print("Processing consumable return...")
                # Bei Verbrauchsmaterial nur den Status in consumable_lendings aktualisieren
                conn.execute('''
                    UPDATE consumable_lendings 
                    SET return_time = CURRENT_TIMESTAMP 
                    WHERE consumable_barcode = ? AND return_time IS NULL
                ''', (item_barcode,))

                # Logging
                conn.execute('''
                    INSERT INTO system_logs 
                    (timestamp, level, message, action, related_barcode)
                    VALUES (CURRENT_TIMESTAMP, 'INFO', ?, 'CONSUMABLE_RETURN', ?)
                ''', (f'Verbrauchsmaterial Ausgabe bestätigt: {item_barcode}', item_barcode))

            conn.commit()
            print("Return processed successfully")
            return jsonify({'success': True, 'message': 'Rückgabe erfolgreich'})

    except Exception as e:
        print(f"Error in process_return: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500