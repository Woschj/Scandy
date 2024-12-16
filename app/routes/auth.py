from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        
        if password == '1234':  # Geändertes Passwort
            session['is_admin'] = True
            return redirect(url_for('admin.dashboard'))
            
        flash('Ungültiges Passwort', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login')) 

@bp.route('/test')
def test():
    return "Test Route funktioniert!"