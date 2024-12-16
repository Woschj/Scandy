from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from ..models.user import User
from ..models.database import Database

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Vereinfachte Login-Logik
    user = User()
    login_user(user)
    session['is_admin'] = True
    return redirect(url_for('admin.dashboard'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index.index')) 