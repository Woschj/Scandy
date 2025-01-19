import sqlite3
from werkzeug.security import generate_password_hash
import os
from app.config import Config
from app.models.database import Database
import logging

logger = logging.getLogger(__name__)

def init_users(app=None):
    """Initialisiert die Benutzerdatenbank"""
    db_path = os.path.join(Config.DATABASE_DIR, 'users.db')
    
    # Erstelle Verzeichnis falls nicht vorhanden
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        
        # Users Tabelle
        cursor.execute('''DROP TABLE IF EXISTS users''')
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Berechtigungstabellen
        cursor.execute('''DROP TABLE IF EXISTS permissions''')
        cursor.execute('''
            CREATE TABLE permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')
        
        cursor.execute('''DROP TABLE IF EXISTS user_permissions''')
        cursor.execute('''
            CREATE TABLE user_permissions (
                user_id INTEGER,
                permission_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (permission_id) REFERENCES permissions(id),
                PRIMARY KEY (user_id, permission_id)
            )
        ''')
        
        # Standard-Admin erstellen
        cursor.execute(
            'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
            ['admin', generate_password_hash('admin'), True]
        )
            
        # Standard-Berechtigungen
        default_permissions = [
            ('tools.view', 'Werkzeuge anzeigen'),
            ('tools.edit', 'Werkzeuge bearbeiten'),
            ('consumables.view', 'Verbrauchsmaterial anzeigen'),
            ('consumables.edit', 'Verbrauchsmaterial bearbeiten'),
            ('workers.view', 'Mitarbeiter anzeigen'),
            ('workers.edit', 'Mitarbeiter bearbeiten'),
            ('admin.view', 'Admin-Bereich anzeigen'),
            ('admin.edit', 'Admin-Bereich bearbeiten')
        ]
        
        for name, description in default_permissions:
            cursor.execute('''
                INSERT INTO permissions (name, description)
                VALUES (?, ?)
            ''', [name, description])
            
        # Dem Admin-User alle Berechtigungen geben
        admin_user = cursor.execute('SELECT id FROM users WHERE username = ?', ['admin']).fetchone()
        if admin_user:
            for name, _ in default_permissions:
                perm = cursor.execute('SELECT id FROM permissions WHERE name = ?', [name]).fetchone()
                if perm:
                    cursor.execute('''
                        INSERT INTO user_permissions (user_id, permission_id)
                        VALUES (?, ?)
                    ''', [admin_user['id'], perm['id']])
        
        conn.commit()
        
    except Exception as e:
        print(f"Fehler bei der Initialisierung der Benutzerdatenbank: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_default_roles():
    """Initialisiert die Standard-Rollen"""
    with Database.get_db() as db:
        cursor = db.cursor()
        
        # Standard-Rollen erstellen
        roles = [
            ('admin', 'Administrator mit allen Rechten'),
            ('user', 'Standardbenutzer')
        ]
        
        for role in roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (name, description)
                VALUES (?, ?)
            ''', role)
            
        db.commit()
        logger.info("Standard-Rollen wurden initialisiert")

def init_permissions():
    """Initialisiert die Berechtigungen und weist sie den Rollen zu"""
    with Database.get_db() as db:
        cursor = db.cursor()
        
        # Standard-Berechtigungen definieren
        permissions = [
            ('tools.view', 'Werkzeuge anzeigen'),
            ('tools.edit', 'Werkzeuge bearbeiten'),
            ('tools.add', 'Werkzeuge hinzufügen'),
            ('tools.delete', 'Werkzeuge löschen'),
            ('consumables.view', 'Verbrauchsmaterial anzeigen'),
            ('consumables.edit', 'Verbrauchsmaterial bearbeiten'),
            ('consumables.add', 'Verbrauchsmaterial hinzufügen'),
            ('consumables.delete', 'Verbrauchsmaterial löschen'),
            ('workers.view', 'Mitarbeiter anzeigen'),
            ('workers.edit', 'Mitarbeiter bearbeiten'),
            ('workers.add', 'Mitarbeiter hinzufügen'),
            ('workers.delete', 'Mitarbeiter löschen'),
            ('admin.view', 'Admin-Bereich anzeigen'),
            ('admin.edit', 'Admin-Einstellungen bearbeiten')
        ]
        
        # Berechtigungen einfügen
        for perm in permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (name, description)
                VALUES (?, ?)
            ''', perm)
        
        # Admin-Rolle alle Berechtigungen zuweisen
        admin_role = cursor.execute(
            'SELECT id FROM roles WHERE name = ?', 
            ['admin']
        ).fetchone()
        
        if admin_role:
            all_permissions = cursor.execute(
                'SELECT id FROM permissions'
            ).fetchall()
            
            for perm in all_permissions:
                cursor.execute('''
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (?, ?)
                ''', [admin_role['id'], perm['id']])
        
        db.commit()
        logger.info("Berechtigungen wurden initialisiert")

if __name__ == '__main__':
    init_users() 