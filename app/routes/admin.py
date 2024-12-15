from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import get_db_connection
from app.utils.decorators import admin_required
from werkzeug.utils import secure_filename
import os
from flask import current_app

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
    with get_db_connection() as conn:
        # Lade die Design-Einstellungen
        colors = {
            'primary': '#5b69a7',  # Standard-Werte
            'secondary': '#4c5789',
            'accent': '#3d4675'
        }
        
        # Hole aktuelle Werte aus der Datenbank
        settings = conn.execute('''
            SELECT key, value FROM settings 
            WHERE key IN ('primary_color', 'secondary_color', 'accent_color')
        ''').fetchall()
        
        # Aktualisiere colors mit Werten aus der DB
        for key, value in settings:
            colors[key.replace('_color', '')] = value

        # Logo-Pfad
        logo = conn.execute('''
            SELECT value FROM settings WHERE key = 'logo_path'
        ''').fetchone()
        current_logo = logo[0] if logo else 'Logo-BTZ-WEISS.svg'

        # Statistiken
        tools_stats = get_tools_stats(conn)
        workers_stats = get_workers_stats(conn)
        consumables_stats = get_consumables_stats(conn)
        current_lendings = get_current_lendings(conn)

        return render_template('admin/dashboard.html',
                             tools_stats=tools_stats,
                             workers_stats=workers_stats,
                             consumables_stats=consumables_stats,
                             current_lendings=current_lendings,
                             colors=colors,
                             current_logo=current_logo)

@bp.route('/update_design', methods=['POST'])
@admin_required
def update_design():
    color_scheme = request.form.get('color_scheme', 'btz')
    schemes = {
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
    """Manuelle Ausleihe/Rückgabe"""
    return render_template('admin/manual_lending.html')

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