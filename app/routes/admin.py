from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g, send_file
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
from werkzeug.security import generate_password_hash
from app.models.settings import Settings
from app.config import Config
import pandas as pd
from io import BytesIO
import openpyxl

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@admin_required
def dashboard():
    """Admin Dashboard"""
    try:
        # Statistiken für Werkzeuge, Mitarbeiter und Verbrauchsmaterial
        stats = {
            'tools': {
                'total': Database.query('SELECT COUNT(*) as count FROM tools WHERE deleted = 0', one=True)['count'],
                'lent': Database.query('SELECT COUNT(*) as count FROM lendings WHERE returned_at IS NULL', one=True)['count'],
                'available': Database.query('SELECT COUNT(*) as count FROM tools WHERE deleted = 0 AND barcode NOT IN (SELECT tool_barcode FROM lendings WHERE returned_at IS NULL)', one=True)['count']
            },
            'workers': {
                'total': Database.query('SELECT COUNT(*) as count FROM workers WHERE deleted = 0', one=True)['count'],
                'active': Database.query('SELECT COUNT(DISTINCT worker_barcode) as count FROM lendings WHERE returned_at IS NULL', one=True)['count']
            },
            'consumables': {
                'total': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0', one=True)['count'],
                'sufficient': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity > min_quantity', one=True)['count'],
                'low': Database.query('SELECT COUNT(*) as count FROM consumables WHERE deleted = 0 AND quantity <= min_quantity', one=True)['count']
            }
        }
        
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
        
        # Aktuelle Materialausgaben
        consumable_usages = Database.query('''
            SELECT cu.*, c.name as consumable_name, w.firstname || ' ' || w.lastname as worker_name
            FROM consumable_usages cu
            JOIN consumables c ON cu.consumable_barcode = c.barcode
            JOIN workers w ON cu.worker_barcode = w.barcode
            ORDER BY cu.used_at DESC
            LIMIT 10
        ''')
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             current_lendings=current_lendings,
                             consumable_usages=consumable_usages)
                            
    except Exception as e:
        flash(f'Fehler beim Laden des Dashboards: {str(e)}', 'error')
        return redirect(url_for('index'))

# Manuelle Ausleihe
@bp.route('/manual-lending', methods=['GET', 'POST'])
@admin_required
def manual_lending():
    """Manuelle Ausleihe/Rückgabe"""
    if request.method == 'POST':
        tool_barcode = request.form.get('tool_barcode')
        worker_barcode = request.form.get('worker_barcode')
        action = request.form.get('action')  # 'lend' oder 'return'
        
        try:
            if action == 'lend':
                Database.query('''
                    INSERT INTO lendings (tool_barcode, worker_barcode, lent_at)
                    VALUES (?, ?, datetime('now'))
                ''', [tool_barcode, worker_barcode])
                flash('Werkzeug erfolgreich ausgeliehen', 'success')
            else:
                Database.query('''
                    UPDATE lendings 
                    SET returned_at = datetime('now')
                    WHERE tool_barcode = ? 
                    AND returned_at IS NULL
                ''', [tool_barcode])
                flash('Werkzeug erfolgreich zurückgegeben', 'success')
                
        except Exception as e:
            flash(f'Fehler: {str(e)}', 'error')
        
        return redirect(url_for('admin.manual_lending'))
        
    return render_template('admin/manual_lending.html')

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
                       CASE WHEN l.returned_at IS NULL 
                            THEN w.firstname || ' ' || w.lastname 
                            ELSE NULL 
                       END as current_borrower
                FROM tools t
                LEFT JOIN lendings l ON t.barcode = l.tool_barcode AND l.returned_at IS NULL
                LEFT JOIN workers w ON l.worker_barcode = w.barcode
                WHERE t.deleted = 0
            ''')
            df = pd.DataFrame(data)
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
            df = pd.DataFrame(data)
            filename = 'mitarbeiter.xlsx'
            
        elif table == 'consumables':
            data = Database.query('''
                SELECT * FROM consumables WHERE deleted = 0
            ''')
            df = pd.DataFrame(data)
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
            df = pd.DataFrame(data)
            filename = 'verlauf.xlsx'
        else:
            return 'Ungültige Tabelle', 400

        # Excel erstellen
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
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
        df = pd.read_excel(file)
        
        if table == 'tools':
            for _, row in df.iterrows():
                Database.query('''
                    INSERT OR REPLACE INTO tools 
                    (barcode, name, description, category, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', [row['barcode'], row['name'], row['description'], 
                     row.get('category'), row.get('location')])
                
        elif table == 'workers':
            for _, row in df.iterrows():
                Database.query('''
                    INSERT OR REPLACE INTO workers 
                    (barcode, firstname, lastname, department, email)
                    VALUES (?, ?, ?, ?, ?)
                ''', [row['barcode'], row['firstname'], row['lastname'],
                     row.get('department'), row.get('email')])
                
        elif table == 'consumables':
            for _, row in df.iterrows():
                Database.query('''
                    INSERT OR REPLACE INTO consumables 
                    (barcode, name, description, quantity, min_quantity, category, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', [row['barcode'], row['name'], row['description'],
                     row['quantity'], row['min_quantity'],
                     row.get('category'), row.get('location')])
                
        flash(f'Import erfolgreich', 'success')
        
    except Exception as e:
        flash(f'Fehler beim Import: {str(e)}', 'error')
        
    return redirect(url_for('admin.dashboard'))

# Weitere Admin-Routen...