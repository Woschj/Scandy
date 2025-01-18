from functools import wraps
from flask import session, redirect, url_for, request, flash, g
from datetime import datetime
from app.utils.logger import loggers
from app.utils.auth_utils import needs_setup
from app.models.database import UserDatabase

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an', 'warning')
            return redirect(url_for('auth.login'))
            
        # Prüfe ob der Benutzer Admin-Rechte hat
        with UserDatabase.get_db() as db:
            user = db.execute('SELECT is_admin FROM users WHERE id = ?', 
                            [session['user_id']]).fetchone()
            
            if not user or not user['is_admin']:
                flash('Sie haben keine Berechtigung für diese Seite', 'error')
                return redirect(url_for('main.index'))
                
        return f(*args, **kwargs)
    return decorated_function

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