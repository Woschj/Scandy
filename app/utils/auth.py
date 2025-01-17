"""
Authentifizierung und Autorisierung
--------------------------------

Dieses Modul handhabt die Benutzerauthentifizierung und Zugriffsrechte in der Anwendung.

Funktionen:
1. Login/Logout-Verwaltung
2. Sitzungsmanagement
3. Zugriffsrechte-Prüfung
4. Passwort-Hashing und Validierung

Benutzerrollen:
- Admin: Voller Zugriff auf alle Funktionen
- Manager: Verwaltung von Werkzeugen und Mitarbeitern
- User: Basis-Zugriff (Ausleihe, Rückgabe)
- Guest: Nur Ansicht bestimmter Seiten

Sicherheitsmerkmale:
- Bcrypt für Passwort-Hashing
- Session-Timeout nach Inaktivität
- CSRF-Schutz für alle Formulare
- IP-basierte Zugriffsbeschränkung

Dekoratoren:
@login_required: Erfordert angemeldeten Benutzer
@admin_required: Erfordert Admin-Rechte
@manager_required: Erfordert Manager-Rechte

Verwendung:
- Von allen Routes verwendet
- Integriert in Template-Rendering
- Automatische Weiterleitung bei fehlenden Rechten
"""

from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function 