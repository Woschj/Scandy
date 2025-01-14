from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.models.database import Database
from urllib.parse import urlparse
from app.models.init_db import init_users
from app.utils.auth_utils import needs_setup

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/')
def index():
    """Hauptroute für Auth"""
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    # Prüfe ob ein Admin-Benutzer existiert
    with Database.get_db() as db:
        user_exists = db.execute('SELECT COUNT(*) FROM users').fetchone()[0] > 0
        
        if not user_exists:
            # Erstelle Standard-Admin mit Passwort 'admin'
            try:
                init_users()
                flash('Standard-Admin-Account wurde erstellt (Passwort: admin)', 'info')
            except Exception as e:
                flash(f'Fehler beim Erstellen des Admin-Accounts: {str(e)}', 'error')
    
    # Wenn bereits eingeloggt, direkt zur Hauptseite
    if session.get('is_admin') and session.get('user_id'):
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login-Versuch für: {username}")  # Debug
        
        user = Database.query('SELECT * FROM users WHERE username = ?', 
                            [username], one=True)
        
        print(f"Gefundener Benutzer: {user}")  # Debug
        
        if user:
            is_valid = check_password_hash(user['password'], password)
            print(f"Passwort-Check: {is_valid}")  # Debug
            
            if is_valid:
                session.clear()
                session['is_admin'] = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                print(f"Login erfolgreich, Session: {dict(session)}")  # Debug
                return redirect(url_for('admin.dashboard'))
            else:
                print(f"Passwort falsch für Benutzer: {username}")  # Debug
        
        flash('Ungültiger Benutzername oder Passwort', 'error')
    
    return render_template('auth/login.html')

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """Ersteinrichtung durchführen"""
    # Prüfe ob bereits ein Admin existiert
    with Database.get_db() as db:
        user_exists = db.execute('SELECT COUNT(*) FROM users').fetchone()[0] > 0
        
        if user_exists:
            flash('Setup wurde bereits durchgeführt', 'warning')
            return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if not password or not confirm:
            flash('Bitte beide Passwörter eingeben', 'error')
            return redirect(url_for('auth.setup'))
            
        if password != confirm:
            flash('Passwörter stimmen nicht überein', 'error')
            return redirect(url_for('auth.setup'))
            
        try:
            if init_users(password=password):
                flash('Setup erfolgreich abgeschlossen', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Setup konnte nicht durchgeführt werden', 'error')
        except Exception as e:
            flash(f'Fehler beim Setup: {str(e)}', 'error')
            
    return render_template('auth/setup.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))