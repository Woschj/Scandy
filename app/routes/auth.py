from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.models.database import Database

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Database.query(
            'SELECT * FROM users WHERE username = ?',
            [username],
            one=True
        )
        
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['is_admin'] = True
            flash('Erfolgreich angemeldet', 'success')
            return redirect(url_for('tools.index'))
            
        flash('Ungültige Anmeldedaten', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Erfolgreich abgemeldet', 'success')
    return render_template('auth/logout.html')