from functools import wraps
from flask import session, redirect, url_for, request, flash, g
from datetime import datetime
from app.utils.logger import loggers
from app.utils.auth_utils import needs_setup
from app.models.database import UserDatabase, Database
from app.models.user import User

def login_required(view):
    """Prüft ob ein Benutzer eingeloggt ist"""
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an', 'error')
            return redirect(url_for('auth.login'))
            
        # Lade den Benutzer in g
        if not hasattr(g, 'user'):
            g.user = User.get(session['user_id'])
            
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    """Prüft ob der Benutzer Admin-Rechte hat"""
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an.', 'error')
            return redirect(url_for('auth.login'))
            
        # Lade den Benutzer in g
        if not hasattr(g, 'user'):
            g.user = User.get(session['user_id'])
            
        if not g.user:
            flash('Bitte melden Sie sich an.', 'error')
            return redirect(url_for('auth.login'))
            
        with Database.get_db() as db:
            # Prüfe ob User Admin ist
            is_admin = db.execute('''
                SELECT EXISTS (
                    SELECT 1 FROM user_roles ur 
                    JOIN roles r ON ur.role_id = r.id 
                    WHERE ur.user_id = ? AND r.name = 'admin'
                ) as is_admin
            ''', [g.user.id]).fetchone()['is_admin']
            
            if not is_admin:
                flash('Sie haben keine Berechtigung für diese Seite.', 'error')
                return redirect(url_for('index.index'))
                
        return view(**kwargs)
    return wrapped_view

def permission_required(permission):
    """Prüft ob ein Benutzer eine bestimmte Berechtigung hat"""
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if 'user_id' not in session:
                flash('Bitte melden Sie sich an', 'error')
                return redirect(url_for('auth.login'))
                
            # Lade den Benutzer in g
            if not hasattr(g, 'user'):
                g.user = User.get(session['user_id'])
                
            if not g.user or not g.user.has_permission(permission):
                flash('Sie haben keine Berechtigung für diese Aktion', 'error')
                return redirect(url_for('main.index'))
                
            return view(**kwargs)
        return wrapped_view
    return decorator

def tech_required(f):
    """Decorator für Techniker-Zugriff (alle eingeloggten Benutzer)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def log_route(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        loggers['user_actions'].info(
            f"Route aufgerufen: {request.endpoint} - "
            f"Methode: {request.method} - "
            f"IP: {request.remote_addr} - "
            f"User-Agent: {request.user_agent} - "
            f"Args: {kwargs}"
        )
        
        if request.form:
            safe_form = {k: v for k, v in request.form.items() if 'password' not in k.lower()}
            loggers['user_actions'].info(f"Form-Daten: {safe_form}")
            
        if request.args:
            loggers['user_actions'].info(f"Query-Parameter: {dict(request.args)}")
            
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            loggers['errors'].error(
                f"Fehler in {request.endpoint}: {str(e)}",
                exc_info=True
            )
            raise
    return decorated_function

def log_db_operation(operation):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = f(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                loggers['database'].info(
                    f"DB Operation: {operation} - "
                    f"Dauer: {duration:.2f}s - "
                    f"Erfolgreich: Ja"
                )
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                loggers['database'].error(
                    f"DB Operation: {operation} - "
                    f"Dauer: {duration:.2f}s - "
                    f"Fehler: {str(e)}"
                )
                raise
        return wrapper
    return decorator 