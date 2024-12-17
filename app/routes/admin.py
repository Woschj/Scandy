from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.models.database import Database
from app.utils.decorators import admin_required
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app.utils.db_schema import SchemaManager
import colorsys

bp = Blueprint('admin', __name__, url_prefix='/admin')

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

def get_current_lendings(conn):
    """Hole aktuelle Ausleihen"""
    return conn.execute('''
        SELECT 
            t.name as tool_name,
            w.firstname || ' ' || w.lastname as worker_name,
            l.lent_at
        FROM lendings l
        JOIN tools t ON t.barcode = l.tool_barcode
        JOIN workers w ON w.barcode = l.worker_barcode
        WHERE l.returned_at IS NULL
        ORDER BY l.lent_at DESC
        LIMIT 5
    ''').fetchall()

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

@bp.route('/dashboard')
@admin_required
def dashboard():
    with Database.get_db() as db:
        cursor = db.cursor()
        
        # Lade die primäre Farbe
        cursor.execute("SELECT value FROM settings WHERE key = 'color_primary'")
        row = cursor.fetchone()
        
        colors = {}
        if row and row['value']:
            hsl_value = row['value']
            print(f"Loaded HSL from DB: {hsl_value}")
            
            try:
                # Konvertiere HSL zu HEX
                h, s, l = map(float, hsl_value.replace('%', '').split())
                h = h / 360
                s = s / 100
                l = l / 100
                
                r, g, b = colorsys.hls_to_rgb(h, l, s)
                hex_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
                
                print(f"Converted HSL {hsl_value} to HEX {hex_color}")  # Debug
                
                colors = {
                    'primary': hsl_value,
                    'primary_hex': hex_color.upper()  # Uppercase für Konsistenz
                }
            except Exception as e:
                print(f"Error converting HSL to HEX: {e}")
                colors = {
                    'primary': '259 94% 51%',
                    'primary_hex': '#3B82F6'
                }
        else:
            colors = {
                'primary': '259 94% 51%',
                'primary_hex': '#3B82F6'
            }
        
        print(f"Final colors for template: {colors}")  # Debug
        
        # Statistiken sammeln
        tools_stats = get_tools_stats(db)
        workers_stats = get_workers_stats(db)
        consumables_stats = get_consumables_stats(db)
        current_lendings = get_current_lendings(db)
        
        # Settings aus der Datenbank holen
        settings = dict(db.execute('''
            SELECT key, value FROM settings
            WHERE key IN ('primary_color', 'accent_color')
        ''').fetchall()) or {
            'primary_color': '#3B82F6',  # Standardwerte
            'accent_color': '#10B981'
        }
        
        stats = {
            'tools_count': tools_stats['total'],
            'tools_lent': tools_stats['lent'],
            'workers_count': workers_stats['total'],
            'consumables_count': consumables_stats['total'],
            'consumables_low': consumables_stats['low_stock'],
            'current_lendings': current_lendings
        }
        
        # Korrekte Blueprint-Routen verwenden
        urls = {
            'tools': url_for('inventory.tools'),
            'workers': url_for('inventory.workers'),
            'consumables': url_for('inventory.consumables'),
            'manual_lending': url_for('admin.manual_lending'),
            'add_tool': url_for('inventory.add_tool'),        # Korrigiert zu inventory
            'add_worker': url_for('inventory.add_worker'),    # Korrigiert zu inventory
            'add_consumable': url_for('inventory.add_consumable')  # Korrigiert zu inventory
        }
        
        return render_template('admin/dashboard.html', 
                             colors=colors,
                             stats=stats,
                             current_lendings=current_lendings)

@bp.route('/update_design', methods=['POST'])
@admin_required
def update_design():
    try:
        hex_color = request.form.get('primary', '#3B82F6')
        print(f"Empfangene HEX Farbe: {hex_color}")  # Debug
        
        # Konvertiere HEX zu RGB
        rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = [x/255.0 for x in rgb]
        
        # Konvertiere RGB zu HSL
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        hsl_value = f"{int(h*360)} {int(s*100)}% {int(l*100)}%"
        print(f"Konvertierte HSL Farbe: {hsl_value}")  # Debug
        
        with Database.get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                ('color_primary', hsl_value)
            )
            db.commit()
            
        return jsonify({
            'status': 'success', 
            'message': 'Design wurde aktualisiert',
            'color': {'hsl': hsl_value, 'hex': hex_color}
        })
        
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Designs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

@bp.route('/manual_lending', methods=['GET'])
@admin_required
def manual_lending():
    tools = Database.query('''
        SELECT id, barcode, name, status 
        FROM tools 
        WHERE deleted = 0
    ''')
    
    workers = Database.query('''
        SELECT id, barcode, firstname, lastname, department 
        FROM workers 
        WHERE deleted = 0
    ''')
    
    consumables = Database.query('''
        SELECT id, barcode, name, quantity, min_quantity 
        FROM consumables 
        WHERE deleted = 0
    ''')
    
    return render_template('admin/manual_lending.html', 
                         tools=tools,
                         workers=workers,
                         consumables=consumables)

@bp.route('/process_lending', methods=['POST'])
@admin_required
def process_lending():
    """Verarbeite manuelle Ausleihe"""
    tool_barcode = request.form.get('tool_barcode')
    worker_barcode = request.form.get('worker_barcode')
    
    with get_db_connection() as conn:
        # Prüfe ob Werkzeug bereits ausgeliehen
        existing = conn.execute('''
            SELECT * FROM lendings 
            WHERE tool_barcode = ? AND returned_at IS NULL
        ''', [tool_barcode]).fetchone()
        
        if existing:
            flash('Werkzeug ist bereits ausgeliehen!', 'error')
            return redirect(url_for('admin.manual_lending'))
        
        # Führe Ausleihe durch
        conn.execute('''
            INSERT INTO lendings (tool_barcode, worker_barcode, lent_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', [tool_barcode, worker_barcode])
        conn.commit()
        
        flash('Ausleihe erfolgreich registriert', 'success')
    return redirect(url_for('admin.manual_lending'))

@bp.route('/process_return', methods=['POST'])
@admin_required
def process_return():
    """Verarbeite manuelle Rückgabe"""
    tool_barcode = request.form.get('tool_barcode')
    
    with get_db_connection() as conn:
        # Prüfe ob Werkzeug ausgeliehen ist
        lending = conn.execute('''
            SELECT * FROM lendings 
            WHERE tool_barcode = ? AND returned_at IS NULL
        ''', [tool_barcode]).fetchone()
        
        if not lending:
            flash('Werkzeug ist nicht ausgeliehen!', 'error')
            return redirect(url_for('admin.manual_lending'))
        
        # Führe Rückgabe durch
        conn.execute('''
            UPDATE lendings 
            SET returned_at = CURRENT_TIMESTAMP
            WHERE tool_barcode = ? AND returned_at IS NULL
        ''', [tool_barcode])
        conn.commit()
        
        flash('Rückgabe erfolgreich registriert', 'success')
    return redirect(url_for('admin.manual_lending'))

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