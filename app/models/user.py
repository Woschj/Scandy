from flask_login import UserMixin
from .database import Database

class User(UserMixin):
    def __init__(self, id, username, is_admin=False):
        self.id = id
        self.username = username
        self.is_admin = is_admin
        self._permissions = None  # Cache für Berechtigungen

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @property
    def permissions(self):
        if self._permissions is None:
            with Database.get_db() as conn:
                self._permissions = {
                    row['name'] for row in conn.execute('''
                        SELECT p.name 
                        FROM permissions p
                        JOIN user_permissions up ON p.id = up.permission_id
                        WHERE up.user_id = ?
                    ''', [self.id])
                }
        return self._permissions

    def has_permission(self, permission):
        """Prüft ob der Benutzer eine bestimmte Berechtigung hat"""
        if self.is_admin:  # Admin hat immer alle Berechtigungen
            return True
        return permission in self.permissions

    @staticmethod
    def get(user_id):
        if not user_id:
            return None
        try:
            with Database.get_db() as conn:
                user = conn.execute('''
                    SELECT u.id, u.username, 
                           EXISTS (
                               SELECT 1 FROM user_roles ur 
                               JOIN roles r ON ur.role_id = r.id 
                               WHERE ur.user_id = u.id AND r.name = 'admin'
                           ) as is_admin
                    FROM users u 
                    WHERE u.id = ?
                ''', [user_id]).fetchone()
                
                if user:
                    return User(user['id'], user['username'], bool(user['is_admin']))
                return None
        except Exception as e:
            print(f"Fehler beim Laden des Users: {e}")
            return None

    # Alias für Flask-Login Kompatibilität
    get_by_id = get