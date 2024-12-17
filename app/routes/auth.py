from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            session['next'] = request.url
            flash('Bitte melden Sie sich als Administrator an.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('is_admin'):
        return redirect(url_for('tools.index'))

    if request.method == 'POST':
        if request.form.get('password') == 'admin123':
            session['is_admin'] = True
            session.permanent = True
            
            next_page = session.get('next')
            if next_page:
                session.pop('next', None)
                return redirect(next_page)
            
            return redirect(url_for('tools.index'))
        
        flash('Falsches Passwort', 'error')
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Erfolgreich abgemeldet', 'success')
    return redirect(url_for('tools.index'))

@bp.route('/test')
def test():
    return "Test Route funktioniert!"