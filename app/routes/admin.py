from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import Database
from app.utils.decorators import admin_required
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app.utils.db_schema import SchemaManager

bp = Blueprint('admin', __name__)

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

@bp.route('/')
@admin_required
def dashboard():
    try:
        with Database.get_db() as conn:
            # Statistiken abrufen
            stats = {
                'tools_count': conn.execute('''
                    SELECT COUNT(*) FROM tools 
                    WHERE deleted = 0
                ''').fetchone()[0],
                
                'consumables_count': conn.execute('''
                    SELECT COUNT(*) FROM consumables 
                    WHERE deleted = 0
                ''').fetchone()[0],
                
                'workers_count': conn.execute('''
                    SELECT COUNT(*) FROM workers 
                    WHERE deleted = 0
                ''').fetchone()[0],
                
                'active_lendings': conn.execute('''
                    SELECT COUNT(*) FROM lendings 
                    WHERE returned_at IS NULL
                ''').fetchone()[0]
            }
            
            # Aktuelle Ausleihen für die Tabelle
            current_lendings = conn.execute('''
                SELECT 
                    t.name as tool_name,
                    w.firstname || ' ' || w.lastname as worker_name,
                    l.lent_at
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                JOIN workers w ON l.worker_barcode = w.barcode
                WHERE l.returned_at IS NULL
                ORDER BY l.lent_at DESC
                LIMIT 10
            ''').fetchall()
            
            # Farbeinstellungen laden
            settings = {}
            for row in conn.execute('SELECT key, value FROM settings').fetchall():
                settings[row['key']] = row['value']
            
            return render_template('admin/dashboard.html',
                                 stats=stats,
                                 current_lendings=current_lendings,
                                 settings=settings)
                                 
    except Exception as e:
        print(f"Fehler im Admin-Dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/update_design', methods=['POST'])
@admin_required
def update_design():
    color_scheme = request.form.get('color_scheme', 'scandy')
    schemes = {
        'scandy': {
            'primary': '#FF4D8D',      # Scandy Pink
            'secondary': '#FF99B9',    # Helles Pink
            'accent': '#FFFFFF',       # Weiß
            'base-100': '#FFF5F8',     # Sehr helles Pink
            'base-200': '#FFE6EE',     
            'base-300': '#FFD6E6',     
            'neutral': '#4A2B39',      # Dunkles Altrosa
            'neutral-focus': '#2D1A23', 
            'navbar-bg': '#FF4D8D',    
            'navbar-text': '#FFFFFF',   
            'sidebar-bg': '#FFF5F8',   
            'card-bg': '#FFFFFF',      
            'footer-bg': '#FF4D8D'     
        },
        'scandy-dark': {
            'primary': '#FF4D8D',      
            'secondary': '#FF99B9',    
            'accent': '#FFFFFF',       
            'base-100': '#2D1A23',     # Dunkles Altrosa
            'base-200': '#4A2B39',     
            'base-300': '#613647',     
            'neutral': '#FFE6EE',      
            'neutral-focus': '#FFFFFF', 
            'navbar-bg': '#2D1A23',    
            'navbar-text': '#FF4D8D',  
            'sidebar-bg': '#4A2B39',   
            'card-bg': '#4A2B39',      
            'footer-bg': '#2D1A23'     
        },
        'btz': {
            'primary': '#6B5CA5',      # BTZ Lila
            'secondary': '#9ED167',    # BTZ Grün
            'accent': '#FFFFFF',       # Weiß
            'base-100': '#FFFFFF',     
            'base-200': '#F8F9FA',     
            'base-300': '#E9ECEF',     
            'neutral': '#2A2A2A',      
            'neutral-focus': '#1A1A1A', 
            'navbar-bg': '#6B5CA5',    
            'navbar-text': '#FFFFFF',   
            'sidebar-bg': '#F8F9FA',   
            'card-bg': '#FFFFFF',      
            'footer-bg': '#6B5CA5'     
        },
        'btz-dark': {
            'primary': '#8B7AB5',      
            'secondary': '#AEE177',    
            'accent': '#FFFFFF',       
            'base-100': '#1F1B24',     
            'base-200': '#2D2733',     
            'base-300': '#3B3342',     
            'neutral': '#E6E6E6',      
            'neutral-focus': '#FFFFFF', 
            'navbar-bg': '#2D2733',    
            'navbar-text': '#E6E6E6',  
            'sidebar-bg': '#1F1B24',   
            'card-bg': '#2D2733',      
            'footer-bg': '#2D2733'     
        },
        'ocean': {
            'primary': '#0EA5E9',      # Hellblau
            'secondary': '#22D3EE',    # Türkis
            'accent': '#F0F9FF',       # Sehr helles Blau
            'base-100': '#F0F9FF',     # Hellblauer Hintergrund
            'base-200': '#E0F2FE',     
            'base-300': '#BAE6FD',     
            'neutral': '#0C4A6E',      # Dunkles Blau für Text
            'neutral-focus': '#082F49', 
            'navbar-bg': '#0369A1',    # Mittelblau
            'navbar-text': '#F0F9FF',  
            'sidebar-bg': '#E0F2FE',   
            'card-bg': '#FFFFFF',      
            'footer-bg': '#0EA5E9'     
        },
        'forest': {
            'primary': '#059669',      # Smaragdgrün
            'secondary': '#10B981',    # Mintgrün
            'accent': '#ECFDF5',       # Sehr helles Grün
            'base-100': '#F0FDF4',     # Hellgrüner Hintergrund
            'base-200': '#DCFCE7',     
            'base-300': '#BBF7D0',     
            'neutral': '#064E3B',      # Dunkelgrün für Text
            'neutral-focus': '#022C22', 
            'navbar-bg': '#047857',    
            'navbar-text': '#ECFDF5',  
            'sidebar-bg': '#DCFCE7',   
            'card-bg': '#FFFFFF',      
            'footer-bg': '#059669'     
        },
        'sunset': {
            'primary': '#EA580C',      # Orange
            'secondary': '#FB923C',    # Helles Orange
            'accent': '#FFF7ED',       # Cremeweiß
            'base-100': '#FFF7ED',     # Warmer Hintergrund
            'base-200': '#FFEDD5',     
            'base-300': '#FED7AA',     
            'neutral': '#7C2D12',      # Dunkelorange für Text
            'neutral-focus': '#431407', 
            'navbar-bg': '#C2410C',    
            'navbar-text': '#FFF7ED',  
            'sidebar-bg': '#FFEDD5',   
            'card-bg': '#FFFFFF',      
            'footer-bg': '#EA580C'     
        },
        'royal': {
            'primary': '#7E22CE',      # Königslila
            'secondary': '#A855F7',    # Helles Lila
            'accent': '#FAF5FF',       # Sehr helles Lila
            'base-100': '#FAF5FF',     # Lilafarbener Hintergrund
            'base-200': '#F3E8FF',     
            'base-300': '#E9D5FF',     
            'neutral': '#581C87',      # Dunkles Lila für Text
            'neutral-focus': '#3B0764', 
            'navbar-bg': '#6B21A8',    
            'navbar-text': '#FAF5FF',  
            'sidebar-bg': '#F3E8FF',   
            'card-bg': '#FFFFFF',      
            'footer-bg': '#7E22CE'     
        }
    }
    
    colors = schemes.get(color_scheme, schemes['btz'])
    with get_db_connection() as conn:
        for key, value in colors.items():
            conn.execute('UPDATE settings SET value = ? WHERE key = ?', 
                        [value, f'{key}_color'])
        conn.commit()

    flash('Design-Einstellungen wurden aktualisiert', 'success')
    return redirect(url_for('admin.dashboard'))

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
    try:
        with Database.get_db() as conn:
            # Debug: Schema überprüfen
            SchemaManager.debug_schema()
            
            # Tools Query mit Debug
            tools_query = SchemaManager.build_select_query(
                'tools',
                columns=['id', 'barcode', 'name', 'status'],
                where='deleted = 0'  # Status-Check erstmal entfernt
            )
            print(f"\nTools Query: {tools_query}")
            tools = conn.execute(tools_query).fetchall()
            print(f"Tools Rohdaten: {tools}")
            
            # Consumables Query mit Debug
            consumables_query = SchemaManager.build_select_query(
                'consumables',
                columns=['id', 'barcode', 'name', 'quantity', 'min_quantity', 'location', 'category'],
                where='deleted = 0'  # Quantity-Check erstmal entfernt
            )
            print(f"\nConsumables Query: {consumables_query}")
            consumables = conn.execute(consumables_query).fetchall()
            print(f"Consumables Rohdaten: {consumables}")
            
            # Workers Query mit Debug
            workers_query = SchemaManager.build_select_query(
                'workers',
                columns=['id', 'barcode', 'firstname', 'lastname', 'department'],
                where='deleted = 0'
            )
            print(f"\nWorkers Query: {workers_query}")
            workers = conn.execute(workers_query).fetchall()
            print(f"Workers Rohdaten: {workers}")
            
            # Lendings Query mit Debug
            lendings_query = """
                SELECT 
                    t.name as tool_name,
                    w.firstname || ' ' || w.lastname as worker_name,
                    l.lent_at,
                    t.barcode as tool_barcode
                FROM lendings l
                JOIN tools t ON l.tool_barcode = t.barcode
                JOIN workers w ON l.worker_barcode = w.barcode
                WHERE l.returned_at IS NULL
            """
            print(f"\nLendings Query: {lendings_query}")
            tool_lendings = conn.execute(lendings_query).fetchall()
            print(f"Lendings Rohdaten: {tool_lendings}")

            # Direkte Tabellen-Überprüfung
            tables_check = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """).fetchall()
            print(f"\nVerfügbare Tabellen: {tables_check}")
            
            # Spalten-Überprüfung für tools
            tools_columns = conn.execute("PRAGMA table_info(tools)").fetchall()
            print(f"\nTools Spalten: {tools_columns}")

            print(f"\nZusammenfassung:")
            print(f"Tools: {len(tools)}")
            print(f"Consumables: {len(consumables)}")
            print(f"Workers: {len(workers)}")
            print(f"Tool Lendings: {len(tool_lendings)}")
            
            return render_template('admin/manual_lending.html',
                                tools=tools,
                                consumables=consumables,
                                workers=workers,
                                tool_lendings=tool_lendings,
                                consumable_lendings=[])
                                
    except Exception as e:
        print(f"Fehler beim Laden der Daten für manuelle Ausleihe: {str(e)}")
        return jsonify({'error': str(e)}), 500

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