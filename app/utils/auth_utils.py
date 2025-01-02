from app.models.database import Database

def needs_setup():
    """Überprüft ob das initiale Setup durchgeführt wurde"""
    admin = Database.query('SELECT * FROM users WHERE username = ?', ['admin'], one=True)
    return admin is None 