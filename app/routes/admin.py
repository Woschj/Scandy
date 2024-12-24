from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.models.database import Database
from app.utils.decorators import admin_required
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app.utils.db_schema import SchemaManager
import colorsys
import logging
from datetime import datetime
from app.models.models import Tool, Consumable, Worker
import sqlite3
from app.utils.error_handler import handle_errors, safe_db_query
from app.utils.color_settings import save_color_setting

bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)

def get_tools_stats(conn):
    """Hole Werkzeug-Statistiken"""
    total = conn.execute('SELECT COUNT(*) FROM tools WHERE deleted = 0').fetchone()[0]
    lent = conn.execute('''
        SELECT COUNT(*) FROM tools t
        JOIN lendings l ON t.barcode = l.tool_barcode
        WHERE t.deleted = 0 AND l.returned_at IS NULL
    ''').fetchone()[0]
    return {'total': total, 'lent': lent}

def get_workers_stats(conn):
    """Hole Mitarbeiter-Statistiken"""
    total = conn.execute('SELECT COUNT(*) FROM workers WHERE deleted = 0').fetchone()[0]
    return {'total': total}

def get_consumables_stats(conn):
    """Hole Verbrauchsmaterial-Statistiken"""
    total = conn.execute('SELECT COUNT(*) FROM consumables WHERE deleted = 0').fetchone()[0]
    low_stock = conn.execute('''
        SELECT COUNT(*) FROM consumables 
        WHERE deleted = 0 AND quantity <= min_quantity
    ''').fetchone()[0]
    return {'total': total, 'low_stock': low_stock}

def get_current_lendings():
    """Holt aktuelle Ausleihen mit zusätzlichen Informationen"""
    with Database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                l.id,
                t.name as tool_name,
                t.barcode as tool_barcode,
                w.firstname || ' ' || w.lastname as worker_name,
                w.barcode as worker_barcode,
                w.department,
                l.lent_at,
                CASE 
                    WHEN julianday('now') - julianday(l.lent_at) > 7 
                    THEN 1 ELSE 0 
                END as overdue
            FROM lendings l
            JOIN tools t ON l.tool_barcode = t.barcode
            JOIN workers w ON l.worker_barcode = w.barcode
            WHERE l.returned_at IS NULL
            ORDER BY l.lent_at DESC
        """)
        
        lendings = []
        for row in cursor.fetchall():
            lendings.append({
                'tool_name': row[1],
                'tool_barcode': row[2],
                'worker_name': row[3],
                'worker_barcode': row[4],
                'department': row[5],
                'lent_at': row[6],
                'overdue': bool(row[7])
            })
        return lendings

def hsl_to_hex(hsl_str):
    """Konvertiert HSL-String zu Hex-Farbe"""
    try:
        h, s, l = map(float, hsl_str.replace('%', '').split())
        h = h / 360
        s = s / 100
        l = l / 100
        
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
    except Exception as e:
        print(f"Fehler bei HSL zu HEX Konvertierung: {e}")
        print(f"HSL String war: {hsl_str}")
        return '#3B82F6'

def get_color_settings():
    """Holt die Farbeinstellungen aus der Datenbank"""
    with Database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'color_primary'")
        row = cursor.fetchone()
        
        if row and row[0]:
            hsl_value = row[0]
            try:
                # Konvertiere HSL zu HEX
                h, s, l = map(float, hsl_value.replace('%', '').split())
                h = h / 360
                s = s / 100
                l = l / 100
                
                r, g, b = colorsys.hls_to_rgb(h, l, s)
                hex_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
                
                return {
                    'primary': hsl_value,
                    'primary_hex': hex_color.upper()  # Uppercase für Konsistenz
                }
            except Exception as e:
                logger.error(f"Error converting HSL to HEX: {e}")
        
        # Standardwerte zurückgeben, wenn keine Einstellungen gefunden wurden
        return {
            'primary': '259 94% 51%',
            'primary_hex': '#3B82F6'
        }

def get_deleted_items():
    """Holt alle gelöschten Items aus der Datenbank"""
    try:
        with Database.get_db() as conn:
            conn.row_factory = sqlite3.Row  # Wichtig: Row Factory setzen
            cursor = conn.cursor()
            
            # Gelöschte Werkzeuge
            cursor.execute("""
                SELECT 
                    'tools' as type,
                    barcode,
                    name,
                    strftime('%d.%m.%Y %H:%M', deleted_at) as deleted_at,
                    category,
                    location
                FROM tools 
                WHERE deleted = 1
                ORDER BY deleted_at DESC
            """)
            deleted_tools = [dict(zip([col[0] for col in cursor.description], row)) 
                           for row in cursor.fetchall()]
            
            # Gelöschte Verbrauchsmaterialien
            cursor.execute("""
                SELECT 
                    'consumables' as type,
                    barcode,
                    name,
                    strftime('%d.%m.%Y %H:%M', deleted_at) as deleted_at,
                    category,
                    location
                FROM consumables 
                WHERE deleted = 1
                ORDER BY deleted_at DESC
            """)
            deleted_consumables = [dict(zip([col[0] for col in cursor.description], row)) 
                                  for row in cursor.fetchall()]
            
            # Gelöschte Mitarbeiter
            cursor.execute("""
                SELECT 
                    'workers' as type,
                    barcode,
                    firstname || ' ' || lastname as name,
                    strftime('%d.%m.%Y %H:%M', deleted_at) as deleted_at,
                    department as category,
                    email as location
                FROM workers 
                WHERE deleted = 1
                ORDER BY deleted_at DESC
            """)
            deleted_workers = [dict(zip([col[0] for col in cursor.description], row)) 
                              for row in cursor.fetchall()]

            print("Gelöschte Items:", {  # Debug-Ausgabe
                'tools': deleted_tools,
                'consumables': deleted_consumables,
                'workers': deleted_workers
            })
            
            return {
                'tools': deleted_tools,
                'consumables': deleted_consumables,
                'workers': deleted_workers
            }
            
    except Exception as e:
        print(f"Fehler beim Laden der gelöschten Items: {e}")
        return {
            'tools': [],
            'consumables': [],
            'workers': []
        }

def get_trash_count():
    """Zählt gelöschte Einträge, robust gegen fehlende Spalten"""
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            total = 0
            
            # Prüfe jede Tabelle einzeln
            for table in ['tools', 'consumables', 'workers']:
                try:
                    columns = [col[1] for col in cursor.execute(f'PRAGMA table_info({table})').fetchall()]
                    if 'deleted' in columns:
                        count = cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE deleted = 1').fetchone()[0]
                        total += count
                except sqlite3.Error as e:
                    print(f"Fehler beim Zählen von {table}: {str(e)}")
                    continue
                    
            return total
    except Exception as e:
        print(f"Fehler beim Ermitteln der Papierkorb-Anzahl: {str(e)}")
        return 0

@bp.route('/dashboard')
@admin_required
@handle_errors
def dashboard():
    def get_consumable_usages():
        """Holt die Verbrauchsmaterial-Nutzungsstatistiken"""
        with Database.get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    c.name as consumable_name,
                    cu.quantity,
                    w.firstname || ' ' || w.lastname as worker_name,
                    cu.used_at
                FROM consumable_usages cu
                JOIN consumables c ON cu.consumable_barcode = c.barcode
                JOIN workers w ON cu.worker_barcode = w.barcode
                WHERE c.deleted = 0
                ORDER BY cu.used_at DESC
                LIMIT 50
            """)
            
            return [
                {
                    'consumable_name': row['consumable_name'],
                    'quantity': row['quantity'],
                    'worker_name': row['worker_name'],
                    'used_at': row['used_at']
                }
                for row in cursor.fetchall()
            ]

    stats = get_stats()
    current_lendings = get_current_lendings()
    consumable_usages = get_consumable_usages()
    colors = get_color_settings()
    deleted_items = get_deleted_items()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         current_lendings=current_lendings,
                         consumable_usages=consumable_usages,
                         colors=colors,
                         deleted_tools=deleted_items['tools'],
                         deleted_consumables=deleted_items['consumables'],
                         deleted_workers=deleted_items['workers'])

@safe_db_query
def get_stats():
    with Database.get_db() as conn:
        # Werkzeug-Statistiken
        tools_stats = conn.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Verfügbar' THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN status = 'Ausgeliehen' THEN 1 ELSE 0 END) as lent,
                SUM(CASE WHEN status = 'Defekt' THEN 1 ELSE 0 END) as defect
            FROM tools 
            WHERE deleted = 0
        ''').fetchone()

        # Verbrauchsmaterial-Statistiken
        consumables_stats = conn.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN quantity > min_quantity THEN 1 ELSE 0 END) as sufficient,
                SUM(CASE WHEN quantity <= min_quantity AND quantity > 0 THEN 1 ELSE 0 END) as low,
                SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) as empty
            FROM consumables 
            WHERE deleted = 0
        ''').fetchone()

        # Mitarbeiter-Statistiken und Abteilungen
        workers_stats = conn.execute('''
            SELECT COUNT(*) as total
            FROM workers 
            WHERE deleted = 0
        ''').fetchone()

        departments = conn.execute('''
            SELECT 
                department as name,
                COUNT(*) as count
            FROM workers 
            WHERE deleted = 0 
            AND department IS NOT NULL 
            GROUP BY department
            ORDER BY department
        ''').fetchall()

        return {
            'tools': {
                'total': tools_stats['total'],
                'available': tools_stats['available'],
                'lent': tools_stats['lent'],
                'defect': tools_stats['defect']
            },
            'tools_count': tools_stats['total'],
            'consumables': {
                'total': consumables_stats['total'],
                'sufficient': consumables_stats['sufficient'],
                'low': consumables_stats['low'],
                'empty': consumables_stats['empty']
            },
            'consumables_count': consumables_stats['total'],
            'workers': {
                'total': workers_stats['total'],
                'departments': [
                    {'name': dept['name'], 'count': dept['count']} 
                    for dept in departments
                ]
            },
            'workers_count': workers_stats['total']
        }

@bp.route('/reset_design', methods=['POST'])
@admin_required
def reset_design():
    default_settings = {
        'logo_path': 'Logo-BTZ-WEISS.svg',
        'primary_color': '#5b69a7',
        'secondary_color': '#4c5789',
        'accent_color': '#3d4675'
    }
    
    with get_db_connection() as conn:
        for key, value in default_settings.items():
            conn.execute('UPDATE settings SET value = ? WHERE key = ?', 
                        [value, key])
        conn.commit()

    return jsonify({'success': True})

@bp.route('/manual_lending')
@admin_required
def manual_lending():
    logger.info("=== Starting manual_lending route ===")
    db = Database()
    try:
        with db.get_db() as conn:
            cursor = conn.cursor()
            
            # Werkzeuge laden
            logger.debug("Executing tools query...")
            tools_query = """
                SELECT 
                    t.id,
                    t.barcode,
                    t.name,
                    t.status
                FROM tools t
                WHERE t.deleted = 0
                ORDER BY t.name
            """
            logger.debug(f"Tools SQL: {tools_query}")
            cursor.execute(tools_query)
            
            tools_raw = cursor.fetchall()
            logger.debug(f"Raw tools data: {tools_raw}")
            
            tools = [
                {
                    'id': row[0],
                    'barcode': row[1],
                    'name': row[2],
                    'status': row[3]
                }
                for row in tools_raw
            ]
            logger.info(f"Loaded {len(tools)} tools")
            logger.debug(f"Processed tools: {tools}")

            # Verbrauchsmaterial laden
            logger.debug("Executing consumables query...")
            consumables_query = """
                SELECT 
                    c.id,
                    c.barcode,
                    c.name,
                    c.quantity
                FROM consumables c
                WHERE c.deleted = 0
                ORDER BY c.name
            """
            logger.debug(f"Consumables SQL: {consumables_query}")
            cursor.execute(consumables_query)
            
            consumables_raw = cursor.fetchall()
            logger.debug(f"Raw consumables data: {consumables_raw}")
            
            consumables = [
                {
                    'id': row[0],
                    'barcode': row[1],
                    'name': row[2],
                    'quantity': row[3]
                }
                for row in consumables_raw
            ]
            logger.info(f"Loaded {len(consumables)} consumables")
            logger.debug(f"Processed consumables: {consumables}")

            # Mitarbeiter laden
            logger.debug("Executing workers query...")
            workers_query = """
                SELECT 
                    w.id,
                    w.barcode,
                    w.firstname,
                    w.lastname,
                    w.department
                FROM workers w
                WHERE w.deleted = 0
                ORDER BY w.lastname, w.firstname
            """
            logger.debug(f"Workers SQL: {workers_query}")
            cursor.execute(workers_query)
            
            workers_raw = cursor.fetchall()
            logger.debug(f"Raw workers data: {workers_raw}")
            
            workers = [
                {
                    'id': row[0],
                    'barcode': row[1],
                    'firstname': row[2],
                    'lastname': row[3],
                    'department': row[4]
                }
                for row in workers_raw
            ]
            logger.info(f"Loaded {len(workers)} workers")
            logger.debug(f"Processed workers: {workers}")

            # Aktuelle Ausleihen laden
            logger.debug("Executing lendings query...")
            lendings_query = """
                SELECT 
                    l.id,
                    t.name as tool_name,
                    t.barcode as tool_barcode,
                    w.firstname || ' ' || w.lastname as worker_name,
                    w.barcode as worker_barcode,
                    l.lent_at,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM consumables c 
                            WHERE c.barcode = t.barcode
                        ) THEN 'Verbrauchsmaterial'
                        ELSE 'Werkzeug'
                    END as category
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                JOIN workers w ON l.worker_barcode = w.barcode
                WHERE l.returned_at IS NULL
                ORDER BY l.lent_at DESC
            """
            logger.debug(f"Lendings SQL: {lendings_query}")
            cursor.execute(lendings_query)
            
            lendings_raw = cursor.fetchall()
            logger.debug(f"Raw lendings data: {lendings_raw}")
            
            current_lendings = []
            for row in lendings_raw:
                lent_at = row[5]
                if lent_at:
                    try:
                        if isinstance(lent_at, str):
                            dt = datetime.strptime(lent_at, '%Y-%m-%d %H:%M:%S')
                        else:
                            dt = lent_at
                        formatted_date = dt.strftime('%d.%m.%Y %H:%M')
                    except (ValueError, TypeError) as e:
                        logger.error(f"Date formatting error: {e}")
                        formatted_date = lent_at
                else:
                    formatted_date = ''

                current_lendings.append({
                    'item_name': row[1],
                    'item_barcode': row[2],
                    'worker_name': row[3],
                    'worker_barcode': row[4],
                    'lent_at': formatted_date,
                    'category': row[6]
                })
            
            logger.info(f"Found {len(current_lendings)} active lendings")
            logger.debug(f"Processed lendings: {current_lendings}")

            logger.debug("Rendering template with data:")
            logger.debug(f"Tools count: {len(tools)}")
            logger.debug(f"Consumables count: {len(consumables)}")
            logger.debug(f"Workers count: {len(workers)}")
            logger.debug(f"Lendings count: {len(current_lendings)}")

            return render_template(
                'admin/manual_lending.html',
                tools=tools,
                consumables=consumables,
                workers=workers,
                current_lendings=current_lendings
            )
            
    except Exception as e:
        logger.error(f"Error in manual_lending route: {str(e)}", exc_info=True)
        flash(f'Fehler beim Laden der Daten: {str(e)}', 'error')
        return render_template(
            'admin/manual_lending.html',
            tools=[],
            consumables=[],
            workers=[],
            current_lendings=[],
            error=str(e)
        )

@bp.route('/process_lending', methods=['POST'])
@admin_required
def process_lending():
    """Verarbeitet eine neue Ausleihe"""
    try:
        data = request.get_json()
        logger.info("=== Starting process_lending ===")
        logger.info(f"Received lending data: {data}")
        
        with Database.get_db() as conn:
            cursor = conn.cursor()
            
            if data['item_type'] == 'consumable':
                logger.info(f"Processing consumable: {data['item_barcode']}")
                
                # Prüfe verfügbare Menge
                cursor.execute("""
                    SELECT id, quantity 
                    FROM consumables 
                    WHERE barcode = ? AND deleted = 0
                """, (data['item_barcode'],))
                consumable = cursor.fetchone()
                
                if not consumable:
                    return jsonify({
                        'success': False,
                        'message': 'Verbrauchsmaterial nicht gefunden'
                    }), 404
                
                if consumable['quantity'] < data['amount']:
                    return jsonify({
                        'success': False,
                        'message': 'Nicht genügend Material verfügbar'
                    }), 400
                
                # Reduziere die Menge
                cursor.execute("""
                    UPDATE consumables 
                    SET quantity = quantity - ? 
                    WHERE id = ?
                """, (data['amount'], consumable['id']))
                  
                cursor.execute("""
                    SELECT id FROM workers
                    WHERE barcode = ?
                """, (data['worker_barcode'],))
                worker_result = cursor.fetchone()
                if not worker_result:
                    return jsonify({
                        'success': False,
                        'message': 'Mitarbeiter nicht gefunden'
                    }), 404
                worker_id = worker_result[0]
                
                # Dann in consumable_usage einfügen
                cursor.execute("""
                    INSERT INTO consumable_usage 
                    (consumable_id, worker_id, quantity) 
                    VALUES (?, ?, ?)
                """, (consumable['id'], worker_id, data['amount']))

            else:
                # Werkzeug-Logik
                logger.info(f"Processing tool: {data['item_barcode']}")
                cursor.execute("""
                    SELECT id, name, status 
                    FROM tools 
                    WHERE barcode = ? AND deleted = 0
                """, (data['item_barcode'],))
                tool = cursor.fetchone()
                
                if not tool:
                    logger.warning(f"Tool not found: {data['item_barcode']}")
                    return jsonify({
                        'success': False,
                        'message': 'Werkzeug nicht gefunden'
                    }), 404

                if tool['status'] != 'Verfügbar':
                    logger.warning(f"Tool not available: {data['item_barcode']}")
                    return jsonify({
                        'success': False,
                        'message': 'Werkzeug ist nicht verfügbar'
                    }), 400

                # Prüfe ob der Worker existiert
                cursor.execute("""
                    SELECT id FROM workers
                    WHERE barcode = ?
                """, (data['worker_barcode'],))
                worker_result = cursor.fetchone()
                if not worker_result:
                    return jsonify({
                        'success': False,
                        'message': 'Mitarbeiter nicht gefunden'
                    }), 404

                cursor.execute("""
                    INSERT INTO lendings 
                    (tool_barcode, worker_barcode, lent_at)
                    VALUES (?, ?, datetime('now'))
                """, (data['item_barcode'], data['worker_barcode']))

                cursor.execute("""
                    UPDATE tools 
                    SET status = 'Ausgeliehen' 
                    WHERE barcode = ?
                """, (data['item_barcode'],))

                logger.info(f"Tool lending recorded")

            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Vorgang erfolgreich durchgeführt'
            })

    except Exception as e:
        logger.error(f"Error in process_lending: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Fehler bei der Verarbeitung: {str(e)}'
        }), 500

@bp.route('/process_return', methods=['POST'])
@admin_required
def process_return():
    logger.info("=== Starting process_return ===")
    
    try:
        data = request.get_json()
        logger.info(f"Received return data: {data}")
        
        if not data or 'item_barcode' not in data:
            return jsonify({
                'success': False,
                'message': 'Kein Barcode übermittelt'
            }), 400

        db = Database()
        
        # Aktuelle Ausleihe finden
        lending = db.get_active_lending(data['item_barcode'])
        logger.info(f"Found lending: {lending}")
        
        if not lending:
            return jsonify({
                'success': False,
                'message': 'Keine aktive Ausleihe gefunden'
            }), 404

        # Rückgabe durchführen
        return_result = db.return_tool(data['item_barcode'])
        logger.info(f"Return result: {return_result}")
        
        if not return_result.get('success'):
            return jsonify(return_result), 400

        # Tool-Status aktualisieren
        update_result = db.update_tool_status(
            barcode=data['item_barcode'],
            status='available'
        )
        logger.info(f"Tool status update result: {update_result}")

        return jsonify({
            'success': True,
            'message': 'Rückgabe erfolgreich durchgeführt'
        })

    except Exception as e:
        logger.error(f"Error in process_return: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Fehler bei der Rückgabe: {str(e)}'
        }), 500

@bp.route('/add_tool', methods=['GET', 'POST'])
@admin_required
def add_tool():
    if request.method == 'POST':
        with Database.get_db() as conn:
            # Daten aus dem Formular holen
            data = {
                'barcode': request.form['barcode'],
                'name': request.form['name'],
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'location': request.form.get('location'),
                'status': request.form.get('status', 'Verfügbar')
            }
            
            # Neues Werkzeug einfügen
            conn.execute('''
                INSERT INTO tools (barcode, name, description, category, location, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (data['barcode'], data['name'], data['description'], 
                  data['category'], data['location'], data['status']))
            
            conn.commit()
            flash('Werkzeug erfolgreich hinzugefügt', 'success')
            return redirect(url_for('inventory.tools'))
    
    # GET-Request: Formular anzeigen
    return render_template('admin/add_tool.html',
                         categories=[],
                         locations=[])

@bp.route('/add_consumable', methods=['GET', 'POST'])
@admin_required
def add_consumable():
    if request.method == 'POST':
        with Database.get_db() as conn:
            # Daten aus dem Formular holen
            data = {
                'barcode': request.form['barcode'],
                'name': request.form['name'],
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'location': request.form.get('location'),
                'quantity': int(request.form.get('quantity', 0)),
                'min_quantity': int(request.form.get('min_quantity', 0))
            }
            
            # Neues Verbrauchsmaterial einfügen
            conn.execute('''
                INSERT INTO consumables (barcode, name, description, category, 
                                      location, quantity, min_quantity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (data['barcode'], data['name'], data['description'], 
                  data['category'], data['location'], data['quantity'], 
                  data['min_quantity']))
            
            conn.commit()
            flash('Verbrauchsmaterial erfolgreich hinzugefügt', 'success')
            return redirect(url_for('inventory.consumables'))
    
    # GET-Request: Formular anzeigen
    return render_template('admin/add_consumable.html',
                         categories=[],
                         locations=[])

@bp.route('/add_worker', methods=['GET', 'POST'])
@admin_required
def add_worker():
    if request.method == 'POST':
        with Database.get_db() as conn:
            # Daten aus dem Formular holen
            data = {
                'barcode': request.form['barcode'],
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'department': request.form.get('department'),
                'email': request.form.get('email')
            }
            
            # Neuen Mitarbeiter einfügen
            conn.execute('''
                INSERT INTO workers (barcode, firstname, lastname, department, email, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (data['barcode'], data['first_name'], data['last_name'], 
                  data['department'], data['email']))
            
            conn.commit()
            flash('Mitarbeiter erfolgreich hinzugefügt', 'success')
            return redirect(url_for('inventory.workers'))
    
    # GET-Request: Formular anzeigen
    with Database.get_db() as conn:
        departments = conn.execute('SELECT DISTINCT department FROM workers').fetchall()
    
    return render_template('admin/add_worker.html',
                         departments=[dep[0] for dep in departments if dep[0]])

@bp.before_app_request
def load_settings():
    """Lädt die Einstellungen vor jeder Anfrage"""
    try:
        with Database.get_db() as conn:
            settings = dict(conn.execute('''
                SELECT key, value FROM settings
                WHERE key IN ('primary_color')
            ''').fetchall()) or {
                'primary_color': '#3B82F6'  # Standardwert
            }
            g.settings = settings
    except Exception as e:
        print(f"Fehler beim Laden der Einstellungen: {str(e)}")
        g.settings = {'primary_color': '#3B82F6'}

@bp.route('/trash')
@admin_required
def trash():
    try:
        deleted_items = get_deleted_items()
        print("DEBUG - Gelöschte Items:", {
            'tools': len(deleted_items['tools']),
            'consumables': len(deleted_items['consumables']),
            'workers': len(deleted_items['workers'])
        })
        print("DEBUG - Beispiel-Tool:", deleted_items['tools'][0] if deleted_items['tools'] else "Keine Tools")
        return render_template('admin/trash.html',
                             deleted_tools=deleted_items['tools'],
                             deleted_consumables=deleted_items['consumables'],
                             deleted_workers=deleted_items['workers'])
    except Exception as e:
        print(f"DEBUG - Fehler in trash route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash(f'Fehler beim Laden des Papierkorbs: {str(e)}', 'error')
        return render_template('error.html', 
                             message='Der Papierkorb konnte nicht geladen werden.', 
                             details=str(e))

@bp.route('/api/settings/colors', methods=['POST'])
def update_colors():
    try:
        data = request.get_json()
        print('Empfangene Farbdaten:', data)
        
        for key, value in data.items():
            print(f'Speichere Farbe: {key} = {value}')
            save_color_setting(f'{key}_color', value)
            
        print('Farben erfolgreich gespeichert')
        return jsonify({'success': True})
    except Exception as e:
        print(f'Fehler beim Speichern der Farben: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/trash/<table>/<barcode>/restore', methods=['POST'])
@admin_required
def restore_from_trash(table, barcode):
    """Stellt einen Eintrag aus dem Papierkorb wieder her"""
    try:
        if Database.restore_item(table, barcode):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Wiederherstellung fehlgeschlagen'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/trash/<table>/<barcode>/delete', methods=['POST'])
@admin_required
def delete_permanently(table, barcode):
    """Löscht einen Eintrag endgültig"""
    try:
        if Database.permanent_delete(table, barcode):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Löschen fehlgeschlagen'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/settings/color', methods=['POST'])
@admin_required
def update_color():
    try:
        data = request.get_json()
        key = data.get('key')
        value = data.get('value')
        
        if not key or not value:
            return jsonify({'success': False, 'message': 'Fehlende Parameter'})
        
        # Speichere HSL-Wert direkt
        save_color_setting(key, value)
        
        # Aktualisiere die Anwendungs-Konfiguration
        g.colors = get_color_settings()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def init_app(app):
    app.register_blueprint(bp)
    
    # Context Processor für globale Template-Variablen
    @app.context_processor
    def utility_processor():
        def get_trash_count():
            try:
                with Database.get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM tools WHERE deleted = 1) +
                            (SELECT COUNT(*) FROM consumables WHERE deleted = 1) +
                            (SELECT COUNT(*) FROM workers WHERE deleted = 1) as total
                    """)
                    return cursor.fetchone()['total']
            except Exception as e:
                print(f"Fehler beim Ermitteln der Papierkorb-Anzahl: {str(e)}")
                return 0
                
        return {
            'trash_count': get_trash_count()
        }