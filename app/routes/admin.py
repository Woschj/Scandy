from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g, send_file
from app.models.database import Database
from app.utils.decorators import admin_required
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app.utils.db_schema import SchemaManager
import colorsys
import logging
from datetime import datetime, timedelta
from app.models.models import Tool, Consumable, Worker
import sqlite3
from app.utils.error_handler import handle_errors, safe_db_query
from app.utils.color_settings import save_color_setting
from werkzeug.security import generate_password_hash
from app.models.settings import Settings
from app.config import Config
import openpyxl
from io import BytesIO
from pathlib import Path
from backup import DatabaseBackup

# Logger einrichten
logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')
backup_manager = DatabaseBackup(app_path=Path(__file__).parent.parent.parent)

def get_recent_activity():
    """Hole die letzten Aktivitäten"""
    return Database.query('''
        SELECT 
            'Ausleihe' as type,
            t.name as item_name,
            w.firstname || ' ' || w.lastname as worker_name,
            l.lent_at as action_date
        FROM lendings l
        JOIN tools t ON l.tool_barcode = t.barcode
        JOIN workers w ON l.worker_barcode = w.barcode
        WHERE l.returned_at IS NULL
        
        UNION ALL
        
        SELECT 
            'Verbrauch' as type,
            c.name as item_name,
            w.firstname || ' ' || w.lastname as worker_name,
            cu.used_at as action_date
        FROM consumable_usages cu
        JOIN consumables c ON cu.consumable_barcode = c.barcode
        JOIN workers w ON cu.worker_barcode = w.barcode
        ORDER BY action_date DESC
        LIMIT 5
    ''')

def get_material_usage():
    """Hole die Materialnutzung"""
    return Database.query('''
        SELECT 
            c.name,
            SUM(CASE WHEN cu.quantity > 0 THEN cu.quantity ELSE 0 END) as total_quantity
        FROM consumable_usages cu
        JOIN consumables c ON cu.consumable_barcode = c.barcode
        GROUP BY c.name
        ORDER BY total_quantity DESC
        LIMIT 5
    ''')

def get_warnings():
    """Hole aktuelle Warnungen"""
    return Database.query('''
        SELECT 
            'Werkzeug defekt' as type,
            name as message,
            'error' as severity
        FROM tools 
        WHERE status = 'defekt' AND deleted = 0
        
        UNION ALL
        
        SELECT 
            'Material niedrig' as type,
            name || ' (Bestand: ' || quantity || ')' as message,
            CASE 
                WHEN quantity < min_quantity * 0.5 THEN 'error'
                ELSE 'warning'
            END as severity
        FROM consumables
        WHERE quantity < min_quantity AND deleted = 0
        ORDER BY severity DESC
        LIMIT 5
    ''')

@bp.route('/')
@admin_required
def dashboard():
    """Admin Dashboard"""
    try:
        # Initialisiere stats Dictionary
        stats = {}
        
        # Hole die finale Liste der Abteilungen
        departments = Database.query('''
            SELECT 
                s.value as name,
                (SELECT COUNT(*) 
                FROM workers w 
                WHERE w.department = s.value 
                AND w.deleted = 0) as worker_count
            FROM settings s
            WHERE s.key LIKE 'department_%'
            AND s.value IS NOT NULL
            AND s.value != ''
            ORDER BY s.value
        ''')
        logger.info(f"=== Abteilungsliste ===")
        logger.info(f"Gefundene Abteilungen: {[dict(d) for d in departments]}")
        stats['departments'] = departments
        
        # Backup-Liste abrufen
        backups = backup_manager.list_backups()
        
        # Hole zuerst die Verbrauchstrend-Daten
        consumable_trend_data = get_consumable_trend()
        
        # Formatiere die Daten für das Chart
        consumable_trend = {
            'labels': [],
            'datasets': []
        }
        
        # Gruppiere die Daten nach Material
        materials = {}
        if consumable_trend_data:
            consumable_trend['labels'] = sorted(set(row['label'] for row in consumable_trend_data))
            for row in consumable_trend_data:
                if row['name'] not in materials:
                    materials[row['name']] = []
                materials[row['name']].append(row['count'])
                
            # Erstelle Datasets für jedes Material
            colors = ['#36A2EB', '#FF6384', '#4BC0C0', '#FF9F40', '#9966FF']
            for i, (name, data) in enumerate(materials.items()):
                consumable_trend['datasets'].append({
                    'label': name,
                    'data': data,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)].replace(')', ', 0.1)'),
                    'borderWidth': 2,
                    'fill': True,
                    'tension': 0.4
                })
        
        stats['consumable_trend'] = consumable_trend
        
        # Statistiken für Werkzeuge und Verbrauchsmaterial
        stats.update({
            'tools': {
                'total': Database.query('SELECT COUNT(*) as count FROM tools WHERE deleted = 0', one=True)['count'],
                'lent': Database.query('SELECT COUNT(*) as count FROM lendings WHERE returned_at IS NULL', one=True)['count'],
                'available': Database.query('''
                    SELECT COUNT(*) as count 
                    FROM tools 
                    WHERE deleted = 0 
                    AND barcode NOT IN (
                        SELECT tool_barcode 
                        FROM lendings 
                        WHERE returned_at IS NULL
                    )
                ''', one=True)['count'],
                'defect': Database.query("SELECT COUNT(*) as count FROM tools WHERE deleted = 0 AND status = 'defekt'", one=True)['count']
            },
            'consumables': {
                'total': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0', one=True)['count'],
                'sufficient': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity >= min_quantity', one=True)['count'],
                'warning': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity < min_quantity AND quantity >= min_quantity * 0.5', one=True)['count'],
                'critical': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity < min_quantity * 0.5', one=True)['count']
            },
            'workers': {
                'total': Database.query('SELECT COUNT(*) as count FROM workers WHERE deleted = 0', one=True)['count'],
                'active_lendings': Database.query('SELECT COUNT(DISTINCT worker_barcode) as count FROM lendings WHERE returned_at IS NULL', one=True)['count']
            }
        })
        
        # Wartungsprobleme (defekte Werkzeuge)
        maintenance_issues = Database.query('''
            SELECT 
                name,
                status,
                CASE 
                    WHEN status = 'defekt' THEN 'error'
                    ELSE 'warning'
                END as severity
            FROM tools
            WHERE status = 'defekt' AND deleted = 0
            LIMIT 5
        ''')
        stats['maintenance_issues'] = maintenance_issues

        # Bestandswarnungen
        inventory_warnings = Database.query('''
            SELECT 
                name as message,
                CASE 
                    WHEN quantity < min_quantity * 0.5 THEN 'error'
                    ELSE 'warning'
                END as type,
                CASE 
                    WHEN quantity < min_quantity * 0.5 THEN 'exclamation-triangle'
                    ELSE 'exclamation'
                END as icon
            FROM consumables
            WHERE quantity < min_quantity AND deleted = 0
            ORDER BY quantity / min_quantity ASC
            LIMIT 5
        ''')
        stats['inventory_warnings'] = inventory_warnings

        # Aktuelle Ausleihen
        current_lendings = Database.query('''
            SELECT l.*, t.name as tool_name, w.firstname || ' ' || w.lastname as worker_name
            FROM lendings l
            JOIN tools t ON l.tool_barcode = t.barcode
            JOIN workers w ON l.worker_barcode = w.barcode
            WHERE l.returned_at IS NULL
            ORDER BY l.lent_at DESC
            LIMIT 10
        ''')
        stats['current_lendings'] = current_lendings

        # Aktuelle Materialausgaben
        consumable_usages = Database.query('''
            SELECT cu.*, c.name as consumable_name, w.firstname || ' ' || w.lastname as worker_name
            FROM consumable_usages cu
            JOIN consumables c ON cu.consumable_barcode = c.barcode
            JOIN workers w ON cu.worker_barcode = w.barcode
            ORDER BY cu.used_at DESC
            LIMIT 10
        ''')
        stats['consumable_usages'] = consumable_usages

        return render_template('admin/dashboard.html', 
                             stats=stats,
                             backups=backups,
                             Config=Config)
                             
    except Exception as e:
        logger.error(f"Fehler im Admin-Dashboard: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash('Fehler beim Laden des Dashboards', 'error')
        return render_template('admin/dashboard.html', 
                             stats={},
                             backups=[],
                             Config=Config)

def get_consumable_trend():
    """Hole die Top 5 Materialverbrauch der letzten 7 Tage"""
    trend_data = Database.query('''
        WITH daily_usage AS (
            SELECT 
                c.name,
                date(cu.used_at) as date,
                SUM(CASE WHEN cu.quantity > 0 THEN cu.quantity ELSE 0 END) as daily_quantity
            FROM consumable_usages cu
            JOIN consumables c ON cu.consumable_barcode = c.barcode
            WHERE cu.used_at >= date('now', '-6 days')
            GROUP BY c.name, date(cu.used_at)
        ),
        dates AS (
            SELECT date('now', '-' || n || ' days') as date
            FROM (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 
                 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6)
        ),
        top_consumables AS (
            SELECT 
                c.name,
                SUM(CASE WHEN cu.quantity > 0 THEN cu.quantity ELSE 0 END) as total_quantity
            FROM consumable_usages cu
            JOIN consumables c ON cu.consumable_barcode = c.barcode
            WHERE cu.used_at >= date('now', '-6 days')
            GROUP BY c.name
            ORDER BY total_quantity DESC
            LIMIT 5
        )
        SELECT 
            dates.date as label,
            tc.name,
            COALESCE(du.daily_quantity, 0) as count
        FROM dates
        CROSS JOIN top_consumables tc
        LEFT JOIN daily_usage du ON dates.date = du.date AND tc.name = du.name
        ORDER BY tc.name, dates.date
    ''')
    
    return trend_data

# Manuelle Ausleihe
@bp.route('/manual-lending', methods=['GET', 'POST'])
@admin_required
def manual_lending():
    """Manuelle Ausleihe/Rückgabe"""
    if request.method == 'POST':
        print("POST-Anfrage empfangen")
        print("Form-Daten:", request.form)
        
        tool_barcode = request.form.get('tool_barcode')
        worker_barcode = request.form.get('worker_barcode')
        action = request.form.get('action')  # 'lend' oder 'return'
        quantity = request.form.get('quantity', type=int)
        
        if not tool_barcode:
            return jsonify({
                'success': False, 
                'message': 'Werkzeug muss ausgewählt sein'
            }), 400
            
        if action == 'lend' and not worker_barcode:
            return jsonify({
                'success': False, 
                'message': 'Mitarbeiter muss ausgewählt sein'
            }), 400
        
        try:
            # Prüfe ob es ein Verbrauchsmaterial ist
            consumable = Database.query('''
                SELECT * FROM consumables 
                WHERE barcode = ? AND deleted = 0
            ''', [tool_barcode], one=True)
            
            if consumable:  # Verbrauchsmaterial-Logik
                if not quantity or quantity <= 0:
                    return jsonify({
                        'success': False,
                        'message': 'Ungültige Menge'
                    }), 400
                    
                if quantity > consumable['quantity']:
                    return jsonify({
                        'success': False,
                        'message': 'Nicht genügend Bestand'
                    }), 400
                    
                # Neue Verbrauchsmaterial-Ausgabe erstellen
                Database.query('''
                    INSERT INTO consumable_usages 
                    (consumable_barcode, worker_barcode, quantity, used_at, modified_at, sync_status)
                    VALUES (?, ?, ?, datetime('now'), datetime('now'), 'pending')
                ''', [tool_barcode, worker_barcode, quantity])
                
                # Bestand aktualisieren
                Database.query('''
                    UPDATE consumables
                    SET quantity = quantity - ?,
                        modified_at = datetime('now'),
                        sync_status = 'pending'
                    WHERE barcode = ?
                ''', [quantity, tool_barcode])
                
                return jsonify({
                    'success': True,
                    'message': 'Verbrauchsmaterial erfolgreich ausgegeben'
                })
            
            # Werkzeug-Logik
            if action == 'lend':
                # Prüfe ob das Werkzeug bereits ausgeliehen ist
                existing_lending = Database.query('''
                    SELECT * FROM lendings
                    WHERE tool_barcode = ?
                    AND returned_at IS NULL
                ''', [tool_barcode], one=True)
                
                if existing_lending:
                    return jsonify({
                        'success': False, 
                        'message': 'Dieses Werkzeug ist bereits ausgeliehen'
                    }), 400
                
                # Neue Ausleihe erstellen
                Database.query('''
                    INSERT INTO lendings (tool_barcode, worker_barcode, lent_at, modified_at, sync_status)
                    VALUES (?, ?, datetime('now'), datetime('now'), 'pending')
                ''', [tool_barcode, worker_barcode])
                
                # Status des Werkzeugs aktualisieren
                Database.query('''
                    UPDATE tools 
                    SET status = 'ausgeliehen',
                        modified_at = datetime('now'),
                        sync_status = 'pending'
                    WHERE barcode = ?
                ''', [tool_barcode])
                
                return jsonify({
                    'success': True, 
                    'message': 'Werkzeug erfolgreich ausgeliehen'
                })
            else:  # action == 'return'
                # Prüfe ob eine aktive Ausleihe existiert
                lending = Database.query('''
                    SELECT * FROM lendings
                    WHERE tool_barcode = ?
                    AND returned_at IS NULL
                ''', [tool_barcode], one=True)
                
                if not lending:
                    return jsonify({
                        'success': False,
                        'message': 'Keine aktive Ausleihe für dieses Werkzeug gefunden'
                    }), 400
                
                # Rückgabe verarbeiten
                Database.query('''
                    UPDATE lendings 
                    SET returned_at = datetime('now'),
                        modified_at = datetime('now'),
                        sync_status = 'pending'
                    WHERE tool_barcode = ? 
                    AND returned_at IS NULL
                ''', [tool_barcode])
                
                # Status des Werkzeugs aktualisieren
                Database.query('''
                    UPDATE tools 
                    SET status = 'verfügbar',
                        modified_at = datetime('now'),
                        sync_status = 'pending'
                    WHERE barcode = ?
                ''', [tool_barcode])
                
                return jsonify({
                    'success': True, 
                    'message': 'Werkzeug erfolgreich zurückgegeben'
                })
                
        except Exception as e:
            print("Fehler bei der Ausleihe:", str(e))
            return jsonify({
                'success': False, 
                'message': f'Fehler: {str(e)}'
            }), 500
            
    # GET request - zeige das Formular
    tools = Database.query('''
        SELECT t.*,
               CASE 
                   WHEN l.id IS NOT NULL THEN 'ausgeliehen'
                   WHEN t.status = 'defekt' THEN 'defekt'
                   ELSE 'verfügbar'
               END as current_status,
               w.firstname || ' ' || w.lastname as lent_to,
               l.lent_at as lending_date
        FROM tools t
        LEFT JOIN (
            SELECT l1.* 
            FROM lendings l1
            LEFT JOIN lendings l2 ON l1.tool_barcode = l2.tool_barcode 
                AND l1.lent_at < l2.lent_at
            WHERE l2.id IS NULL 
            AND l1.returned_at IS NULL
        ) l ON t.barcode = l.tool_barcode
        LEFT JOIN workers w ON l.worker_barcode = w.barcode
        WHERE t.deleted = 0
        ORDER BY t.name
    ''')

    workers = Database.query('''
        SELECT * FROM workers WHERE deleted = 0
        ORDER BY lastname, firstname
    ''')

    consumables = Database.query('''
        SELECT * FROM consumables WHERE deleted = 0
        ORDER BY name
    ''')

    # Aktuelle Ausleihen (Werkzeuge und Verbrauchsmaterial)
    current_lendings = Database.query('''
        WITH RECURSIVE current_tool_lendings AS (
            SELECT 
                l.id,
                t.name as item_name,
                t.barcode as item_barcode,
                w.firstname || ' ' || w.lastname as worker_name,
                w.barcode as worker_barcode,
                'Werkzeug' as category,
                l.lent_at as action_date,
                NULL as amount
            FROM lendings l
            JOIN tools t ON l.tool_barcode = t.barcode
            JOIN workers w ON l.worker_barcode = w.barcode
            WHERE l.returned_at IS NULL
            AND t.deleted = 0
            AND w.deleted = 0
        ),
        current_consumable_usages AS (
            SELECT 
                cu.id,
                c.name as item_name,
                c.barcode as item_barcode,
                w.firstname || ' ' || w.lastname as worker_name,
                w.barcode as worker_barcode,
                'Verbrauchsmaterial' as category,
                cu.used_at as action_date,
                cu.quantity as amount
            FROM consumable_usages cu
            JOIN consumables c ON cu.consumable_barcode = c.barcode
            JOIN workers w ON cu.worker_barcode = w.barcode
            WHERE DATE(cu.used_at) >= DATE('now', '-7 days')
            AND c.deleted = 0
            AND w.deleted = 0
        )
        SELECT * FROM current_tool_lendings
        UNION ALL
        SELECT * FROM current_consumable_usages
        ORDER BY action_date DESC
    ''')

    return render_template('admin/manual_lending.html', 
                          tools=tools,
                          workers=workers,
                          consumables=consumables,
                          current_lendings=current_lendings)

@bp.route('/trash')
@admin_required
def trash():
    """Papierkorb mit gelöschten Einträgen"""
    tools = Database.query('''
        SELECT * FROM tools WHERE deleted = 1
    ''')
    consumables = Database.query('''
        SELECT * FROM consumables WHERE deleted = 1
    ''')
    workers = Database.query('''
        SELECT * FROM workers WHERE deleted = 1
    ''')
    
    return render_template('admin/trash.html',
                         tools=tools,
                         consumables=consumables,
                         workers=workers)

@bp.route('/tools/<barcode>/delete', methods=['DELETE'])
@admin_required
def delete_tool(barcode):
    """Werkzeug in den Papierkorb verschieben"""
    try:
        Database.query('''
            UPDATE tools 
            SET deleted = 1,
                deleted_at = datetime('now'),
                modified_at = datetime('now'),
                sync_status = 'pending'
            WHERE barcode = ?
        ''', [barcode])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/consumables/<barcode>/delete', methods=['DELETE'])
@admin_required
def delete_consumable(barcode):
    """Verbrauchsmaterial in den Papierkorb verschieben"""
    try:
        Database.query('''
            UPDATE consumables 
            SET deleted = 1,
                deleted_at = datetime('now'),
                modified_at = datetime('now'),
                sync_status = 'pending'
            WHERE barcode = ?
        ''', [barcode])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/workers/<barcode>/delete', methods=['DELETE'])
@admin_required
def delete_worker(barcode):
    """Mitarbeiter in den Papierkorb verschieben"""
    try:
        Database.query('''
            UPDATE workers 
            SET deleted = 1,
                deleted_at = datetime('now'),
                modified_at = datetime('now'),
                sync_status = 'pending'
            WHERE barcode = ?
        ''', [barcode])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/trash/restore/<type>/<barcode>', methods=['POST'])
@admin_required
def restore_item(type, barcode):
    """Element aus dem Papierkorb wiederherstellen"""
    try:
        table = {
            'tool': 'tools',
            'consumable': 'consumables',
            'worker': 'workers'
        }.get(type)
        
        if not table:
            return jsonify({'success': False, 'error': 'Ungültiger Typ'}), 400
            
        Database.query(f'''
            UPDATE {table}
            SET deleted = 0,
                deleted_at = NULL,
                modified_at = datetime('now'),
                sync_status = 'pending'
            WHERE barcode = ?
        ''', [barcode])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/server-settings', methods=['GET', 'POST'])
@admin_required
def server_settings():
    if request.method == 'POST':
        mode = request.form.get('mode')
        server_url = request.form.get('server_url')
        
        try:
            # Speichere Einstellungen in der Datenbank
            Database.query('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', ['server_mode', '1' if mode == 'server' else '0'])
            
            if mode == 'client' and server_url:
                Database.query('''
                    INSERT OR REPLACE INTO settings (key, value)
                    VALUES (?, ?)
                ''', ['server_url', server_url])
            
            if mode == 'server':
                Config.init_server()
                flash('Server-Modus aktiviert', 'success')
            else:
                Config.init_client(server_url)
                flash('Client-Modus aktiviert', 'success')
                
        except Exception as e:
            flash(f'Fehler beim Speichern der Einstellungen: {str(e)}', 'error')
            return redirect(url_for('admin.server_settings'))
            
    try:
        # Hole aktuelle Einstellungen
        status = Database.query('''
            SELECT last_sync, status, error 
            FROM sync_status 
            ORDER BY id DESC LIMIT 1
        ''', one=True)
        
        auto_sync = Database.query('''
            SELECT value FROM settings
            WHERE key = 'auto_sync'
        ''', one=True)
                
        return render_template('admin/server_settings.html',
                             is_server=Config.SERVER_MODE,
                             server_url=Config.SERVER_URL,
                             last_sync=status['last_sync'] if status else None,
                             sync_status=status['status'] if status else 'never',
                             sync_error=status['error'] if status else None,
                             auto_sync=bool(int(auto_sync['value'])) if auto_sync else False)
                             
    except Exception as e:
        flash(f'Fehler beim Laden der Einstellungen: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/export/<table>')
@admin_required
def export_table(table):
    """Exportiert eine Tabelle als Excel"""
    try:
        if table == 'tools':
            data = Database.query('''
                SELECT t.*, 
                       w.firstname || ' ' || w.lastname as lent_to
                FROM tools t
                LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.deleted = 0
            ''')
            headers = ['barcode', 'name', 'description', 'category', 'location', 'status', 'lent_to']
            filename = 'werkzeuge.xlsx'
            
        elif table == 'workers':
            data = Database.query('''
                SELECT w.*, 
                       COUNT(DISTINCT l.id) as active_lendings
                FROM workers w
                LEFT JOIN lendings l ON w.barcode = l.worker_barcode AND l.returned_at IS NULL
                WHERE w.deleted = 0
                GROUP BY w.id
            ''')
            headers = ['barcode', 'firstname', 'lastname', 'department', 'active_lendings']
            filename = 'mitarbeiter.xlsx'
            
        elif table == 'consumables':
            data = Database.query('''
                SELECT * FROM consumables WHERE deleted = 0
            ''')
            headers = ['barcode', 'name', 'description', 'category', 'location', 'quantity', 'min_quantity']
            filename = 'verbrauchsmaterial.xlsx'
            
        elif table == 'history':
            data = Database.query('''
                SELECT 
                    'Werkzeug' as type,
                    t.name as item_name,
                    w.firstname || ' ' || w.lastname as worker_name,
                    l.lent_at,
                    l.returned_at,
                    NULL as quantity
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                JOIN workers w ON l.worker_barcode = w.barcode
                
                UNION ALL
                
                SELECT 
                    'Verbrauchsmaterial' as type,
                    c.name as item_name,
                    w.firstname || ' ' || w.lastname as worker_name,
                    cu.used_at as lent_at,
                    cu.used_at as returned_at,
                    cu.quantity
                FROM consumable_usages cu
                JOIN consumables c ON cu.consumable_barcode = c.barcode
                JOIN workers w ON cu.worker_barcode = w.barcode
                ORDER BY lent_at DESC
            ''')
            headers = ['type', 'item_name', 'worker_name', 'lent_at', 'returned_at', 'quantity']
            filename = 'verlauf.xlsx'
        else:
            return 'Ungültige Tabelle', 400

        # Excel erstellen
        wb = openpyxl.Workbook()
        ws = wb.active
        
        # Headers schreiben
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # Daten schreiben
        for row_idx, row_data in enumerate(data, 2):
            for col_idx, header in enumerate(headers, 1):
                ws.cell(row=row_idx, column=col_idx, value=row_data.get(header))
        
        # Excel in BytesIO speichern
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f'Fehler beim Export: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/import/<table>', methods=['POST'])
@admin_required
def import_table(table):
    """Importiert eine Excel-Tabelle"""
    if 'file' not in request.files:
        flash('Keine Datei ausgewählt', 'error')
        return redirect(url_for('admin.dashboard'))
        
    file = request.files['file']
    if file.filename == '':
        flash('Keine Datei ausgewählt', 'error')
        return redirect(url_for('admin.dashboard'))

    try:
        # Excel-Datei in BytesIO laden
        file_content = BytesIO(file.read())
        wb = openpyxl.load_workbook(file_content)
        ws = wb.active
        
        # Headers aus erster Zeile lesen
        headers = [cell.value for cell in ws[1]]
        
        if table == 'tools':
            for row in ws.iter_rows(min_row=2):
                row_data = {headers[i]: cell.value for i, cell in enumerate(row)}
                Database.query('''
                    INSERT OR REPLACE INTO tools 
                    (barcode, name, description, category, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', [row_data.get('barcode'), row_data.get('name'), 
                     row_data.get('description'), row_data.get('category'), 
                     row_data.get('location')])
                
        elif table == 'workers':
            for row in ws.iter_rows(min_row=2):
                row_data = {headers[i]: cell.value for i, cell in enumerate(row)}
                Database.query('''
                    INSERT OR REPLACE INTO workers 
                    (barcode, firstname, lastname, department, email)
                    VALUES (?, ?, ?, ?, ?)
                ''', [row_data.get('barcode'), row_data.get('firstname'), row_data.get('lastname'),
                     row_data.get('department'), row_data.get('email')])
                
        elif table == 'consumables':
            for row in ws.iter_rows(min_row=2):
                row_data = {headers[i]: cell.value for i, cell in enumerate(row)}
                Database.query('''
                    INSERT OR REPLACE INTO consumables 
                    (barcode, name, description, quantity, min_quantity, category, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', [row_data.get('barcode'), row_data.get('name'), row_data.get('description'),
                     row_data.get('quantity'), row_data.get('min_quantity'),
                     row_data.get('category'), row_data.get('location')])
                
        flash(f'Import erfolgreich', 'success')
        
    except Exception as e:
        flash(f'Fehler beim Import: {str(e)}', 'error')
        
    return redirect(url_for('admin.dashboard'))

@bp.route('/backup/create', methods=['POST'])
@admin_required
def create_backup():
    """Manuelles Backup erstellen"""
    try:
        logger.info("Starte manuelles Backup...")
        success = backup_manager.create_backup()
        if success:
            flash('Backup wurde erfolgreich erstellt', 'success')
            logger.info("Backup erfolgreich erstellt")
        else:
            flash('Fehler beim Erstellen des Backups', 'error')
            logger.error("Backup konnte nicht erstellt werden")
    except Exception as e:
        error_msg = f'Fehler beim Erstellen des Backups: {str(e)}'
        logger.error(error_msg)
        flash(error_msg, 'error')
    return redirect(url_for('admin.dashboard'))

@bp.route('/backup/restore/<filename>', methods=['POST'])
@admin_required
def restore_backup(filename):
    """Backup wiederherstellen"""
    try:
        logger.info(f"Versuche Backup wiederherzustellen: {filename}")
        backup_path = backup_manager.backup_dir / filename
        if not backup_path.exists():
            error_msg = 'Backup-Datei nicht gefunden'
            logger.error(f"{error_msg}: {backup_path}")
            flash(error_msg, 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Datenbank wiederherstellen
        success = backup_manager.restore_backup(filename)
        if success:
            success_msg = 'Backup wurde erfolgreich wiederhergestellt'
            logger.info(success_msg)
            flash(success_msg, 'success')
        else:
            error_msg = 'Fehler bei der Wiederherstellung des Backups'
            logger.error(error_msg)
            flash(error_msg, 'error')
    except Exception as e:
        error_msg = f'Fehler beim Wiederherstellen des Backups: {str(e)}'
        logger.error(error_msg)
        flash(error_msg, 'error')
    return redirect(url_for('admin.dashboard'))

@bp.route('/departments', methods=['GET'])
def get_departments():
    """Gibt alle Abteilungen zurück."""
    try:
        departments = Database.get_departments()
        print("Abteilungen geladen:", departments)  # Debug-Log
        return jsonify({
            'success': True,
            'departments': departments
        })
    except Exception as e:
        print("Fehler beim Laden der Abteilungen:", str(e))  # Debug-Log
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/departments/add', methods=['POST'])
def add_department():
    """Fügt eine neue Abteilung hinzu."""
    name = request.form.get('department')
    if not name:
        return jsonify({
            'success': False,
            'message': 'Kein Name angegeben'
        })

    success = Database.add_department(name)
    return jsonify({
        'success': success,
        'message': 'Abteilung erfolgreich hinzugefügt' if success else 'Fehler beim Hinzufügen der Abteilung'
    })

@bp.route('/departments/delete/<name>', methods=['DELETE'])
def delete_department(name):
    """Löscht eine Abteilung."""
    success, message = Database.delete_department(name)
    return jsonify({
        'success': success,
        'message': message
    })

@bp.route('/locations', methods=['GET'])
def get_locations():
    """Gibt alle Standorte zurück."""
    usage = request.args.get('usage')  # Optional: 'tools' oder 'consumables'
    locations = Database.get_locations(usage)
    return jsonify({
        'success': True,
        'locations': locations
    })

@bp.route('/locations/add', methods=['POST'])
def add_location():
    """Fügt einen neuen Standort hinzu."""
    name = request.form.get('location')
    if not name:
        return jsonify({
            'success': False,
            'message': 'Kein Name angegeben'
        })

    success = Database.add_location(name)
    return jsonify({
        'success': success,
        'message': 'Standort erfolgreich hinzugefügt' if success else 'Fehler beim Hinzufügen des Standorts'
    })

@bp.route('/locations/<name>/usage', methods=['PUT'])
def update_location_usage(name):
    """Aktualisiert den Verwendungszweck eines Standorts."""
    data = request.get_json()
    usage = data.get('usage')
    if not usage:
        return jsonify({
            'success': False,
            'message': 'Keine Verwendung angegeben'
        })

    success = Database.update_location_usage(name, usage)
    return jsonify({
        'success': success,
        'message': 'Verwendung erfolgreich aktualisiert' if success else 'Fehler beim Aktualisieren der Verwendung'
    })

@bp.route('/locations/delete/<name>', methods=['DELETE'])
def delete_location(name):
    """Löscht einen Standort."""
    success, message = Database.delete_location(name)
    return jsonify({
        'success': success,
        'message': message
    })

@bp.route('/categories', methods=['GET'])
def get_categories():
    """Gibt alle Kategorien zurück."""
    usage = request.args.get('usage')  # Optional: 'tools' oder 'consumables'
    categories = Database.get_categories(usage)
    return jsonify({
        'success': True,
        'categories': categories
    })

@bp.route('/categories/add', methods=['POST'])
def add_category():
    """Fügt eine neue Kategorie hinzu."""
    name = request.form.get('category')
    if not name:
        return jsonify({
            'success': False,
            'message': 'Kein Name angegeben'
        })

    success = Database.add_category(name)
    return jsonify({
        'success': success,
        'message': 'Kategorie erfolgreich hinzugefügt' if success else 'Fehler beim Hinzufügen der Kategorie'
    })

@bp.route('/categories/<name>/usage', methods=['PUT'])
def update_category_usage(name):
    """Aktualisiert den Verwendungszweck einer Kategorie."""
    data = request.get_json()
    usage = data.get('usage')
    if not usage:
        return jsonify({
            'success': False,
            'message': 'Keine Verwendung angegeben'
        })

    success = Database.update_category_usage(name, usage)
    return jsonify({
        'success': success,
        'message': 'Verwendung erfolgreich aktualisiert' if success else 'Fehler beim Aktualisieren der Verwendung'
    })

@bp.route('/categories/delete/<name>', methods=['DELETE'])
def delete_category(name):
    """Löscht eine Kategorie."""
    success, message = Database.delete_category(name)
    return jsonify({
        'success': success,
        'message': message
    })

# Weitere Admin-Routen...