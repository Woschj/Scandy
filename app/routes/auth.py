from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.models.database import Database
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
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            session['is_admin'] = True
            session['user_id'] = 'admin'
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Ungültige Anmeldedaten', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.route('/test')
def test():
    return "Test Route funktioniert!"