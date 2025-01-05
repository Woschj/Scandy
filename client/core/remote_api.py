import requests
from urllib.parse import urljoin

class RemoteAPI:
    def __init__(self, server_url=None):
        self.server_url = server_url or "http://localhost:5000"
        self.session = requests.Session()
        
    def _get(self, endpoint):
        """GET-Request an den Server"""
        try:
            response = self.session.get(urljoin(self.server_url, endpoint))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API-Fehler (GET {endpoint}): {str(e)}")
            return None
            
    def _post(self, endpoint, data=None):
        """POST-Request an den Server"""
        try:
            response = self.session.post(urljoin(self.server_url, endpoint), json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API-Fehler (POST {endpoint}): {str(e)}")
            return None
            
    def login(self, username, password):
        """Benutzer anmelden"""
        response = self._post('/auth/login', {
            'username': username,
            'password': password
        })
        return response and response.get('success', False)
        
    def setup(self, username, password):
        """Ersteinrichtung durchführen"""
        response = self._post('/auth/setup', {
            'username': username,
            'password': password
        })
        return response and response.get('success', False)
        
    def needs_setup(self):
        """Prüft ob Ersteinrichtung notwendig ist"""
        response = self._get('/auth/needs_setup')
        return response and response.get('needs_setup', True)
        
    def get_tools(self):
        """Holt alle Werkzeuge"""
        response = self._get('/api/tools')
        return response and response.get('tools', [])
        
    def get_workers(self):
        """Holt alle Mitarbeiter"""
        response = self._get('/api/workers')
        return response and response.get('workers', [])
        
    def get_consumables(self):
        """Holt alle Verbrauchsmaterialien"""
        response = self._get('/api/consumables')
        return response and response.get('consumables', [])
        
    def create_lending(self, tool_barcode, worker_barcode):
        """Erstellt eine neue Ausleihe"""
        response = self._post('/api/lendings/create', {
            'tool_barcode': tool_barcode,
            'worker_barcode': worker_barcode
        })
        return response and response.get('success', False)
        
    def return_tool(self, tool_barcode):
        """Gibt ein Werkzeug zurück"""
        response = self._post('/api/lendings/return', {
            'tool_barcode': tool_barcode
        })
        return response and response.get('success', False) 