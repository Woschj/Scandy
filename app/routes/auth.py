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
    # Wenn Setup benötigt wird und wir nicht bereits auf der Setup-Seite sind
    if needs_setup() and not request.endpoint == 'auth.setup':
        return redirect(url_for('auth.setup'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Database.query('SELECT * FROM users WHERE username = ?', 
                            [username], one=True)
        
        if user and check_password_hash(user['password'], password):
            session['is_admin'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Hole die next URL aus den Argumenten
            next_url = request.args.get('next')
            
            # Wenn keine next URL vorhanden oder ungültig, gehe zur Hauptseite
            if not next_url or not next_url.startswith('/'):
                next_url = url_for('tools.index')
                
            return redirect(next_url)
            
        flash('Ungültiger Benutzername oder Passwort', 'error')
    
    return render_template('auth/login.html')

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """Ersteinrichtung der Anwendung"""
    # Wenn Setup bereits durchgeführt wurde
    if not needs_setup():
        flash('Setup wurde bereits durchgeführt', 'info')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not password:
            flash('Bitte ein Passwort eingeben', 'error')
        elif password != password_confirm:
            flash('Passwörter stimmen nicht überein', 'error')
        elif len(password) < 8:
            flash('Passwort muss mindestens 8 Zeichen lang sein', 'error')
        else:
            try:
                if init_users(password):
                    flash('Setup erfolgreich abgeschlossen', 'success')
                    return redirect(url_for('auth.login'))
            except Exception as e:
                print(f"Setup-Fehler: {str(e)}")
                flash(f'Fehler beim Setup: {str(e)}', 'error')
    
    # Direkt das Setup-Template rendern, ohne base.html
    return render_template('auth/setup.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))