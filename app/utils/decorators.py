from functools import wraps
from flask import session, redirect, url_for
from flask_login import current_user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
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