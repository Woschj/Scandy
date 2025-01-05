from app.models.database import Database
from app.models.tool import Tool
from app.models.worker import Worker
from app.models.consumable import Consumable
from app.models.user import User

class ScandyClient:
    def __init__(self, mode='standalone'):
        """
        Initialisiert den Scandy-Client
        
        :param mode: 'standalone' oder 'server'
        """
        self.mode = mode
        self._logged_in = False
        self._user = None
        
    def login(self, username, password):
        """Benutzer anmelden"""
        try:
            user = User.authenticate(username, password)
            if user:
                self._logged_in = True
                self._user = user
                return True
        except Exception as e:
            print(f"Login-Fehler: {str(e)}")
        return False
        
    def logout(self):
        """Benutzer abmelden"""
        self._logged_in = False
        self._user = None
        
    def is_logged_in(self):
        """Prüft ob ein Benutzer angemeldet ist"""
        return self._logged_in
        
    def get_current_user(self):
        """Gibt den aktuellen Benutzer zurück"""
        return self._user
        
    def get_tool_stats(self):
        """Gibt Statistiken über Werkzeuge zurück"""
        try:
            with Database.get_db() as db:
                total = Tool.count()
                available = Tool.count_available()
                lent = Tool.count_lent()
                defect = Tool.count_defect()
                
                return {
                    "total": total,
                    "Verfügbar": available,
                    "Ausgeliehen": lent,
                    "Defekt": defect
                }
        except Exception as e:
            print(f"Fehler beim Abrufen der Werkzeug-Statistiken: {str(e)}")
            return {
                "total": 0,
                "Verfügbar": 0,
                "Ausgeliehen": 0,
                "Defekt": 0
            }
        
    def get_consumables_stats(self):
        """Gibt Statistiken über Verbrauchsmaterial zurück"""
        try:
            with Database.get_db() as db:
                total = Consumable.count()
                available = Consumable.count_sufficient()
                warning = Consumable.count_warning()
                
                return {
                    "total": total,
                    "Verfügbar": available,
                    "Nachbestellen": warning
                }
        except Exception as e:
            print(f"Fehler beim Abrufen der Material-Statistiken: {str(e)}")
            return {
                "total": 0,
                "Verfügbar": 0,
                "Nachbestellen": 0
            }
        
    def get_worker_stats(self):
        """Gibt Statistiken über Mitarbeiter zurück"""
        try:
            with Database.get_db() as db:
                total = Worker.count()
                active = Worker.count_active()
                inactive = Worker.count_inactive()
                
                return {
                    "total": total,
                    "Aktiv": active,
                    "Inaktiv": inactive
                }
        except Exception as e:
            print(f"Fehler beim Abrufen der Mitarbeiter-Statistiken: {str(e)}")
            return {
                "total": 0,
                "Aktiv": 0,
                "Inaktiv": 0
            }
        
    def get_tools(self):
        """Gibt Liste aller Werkzeuge zurück"""
        try:
            return Tool.get_all()
        except Exception as e:
            print(f"Fehler beim Abrufen der Werkzeuge: {str(e)}")
            return []
            
    def get_workers(self):
        """Gibt Liste aller Mitarbeiter zurück"""
        try:
            return Worker.get_all()
        except Exception as e:
            print(f"Fehler beim Abrufen der Mitarbeiter: {str(e)}")
            return []
            
    def get_consumables(self):
        """Gibt Liste aller Verbrauchsmaterialien zurück"""
        try:
            return Consumable.get_all()
        except Exception as e:
            print(f"Fehler beim Abrufen der Verbrauchsmaterialien: {str(e)}")
            return []
            
    def create_lending(self, tool_barcode, worker_barcode):
        """Erstellt eine neue Ausleihe"""
        try:
            with Database.get_db() as db:
                Tool.lend(tool_barcode, worker_barcode)
                return True
        except Exception as e:
            print(f"Fehler beim Erstellen der Ausleihe: {str(e)}")
            return False
            
    def return_tool(self, tool_barcode):
        """Gibt ein Werkzeug zurück"""
        try:
            with Database.get_db() as db:
                Tool.return_tool(tool_barcode)
                return True
        except Exception as e:
            print(f"Fehler bei der Werkzeugrückgabe: {str(e)}")
            return False 