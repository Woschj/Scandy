class Routes:
    """Zentrale Route-Definitionen"""
    # Hauptrouten
    INDEX = 'inventory.tools'
    
    # Admin-Bereich
    ADMIN_DASHBOARD = 'admin.dashboard'
    ADMIN_LOGS = 'admin.logs'
    ADMIN_MANUAL_LENDING = 'admin.manual_lending'
    
    # Auth
    LOGIN = 'auth.login'
    LOGOUT = 'auth.logout'
    
    # Werkzeuge
    TOOLS_INDEX = 'inventory.tools'
    TOOLS_ADD = 'inventory.add_tool'
    TOOLS_DETAILS = 'inventory.tool_details'
    
    # Verbrauchsmaterial
    CONSUMABLES_INDEX = 'inventory.consumables'
    CONSUMABLES_ADD = 'inventory.add_consumable'
    CONSUMABLES_DETAILS = 'inventory.consumable_details'
    
    # Mitarbeiter
    WORKERS_INDEX = 'inventory.workers'
    WORKERS_ADD = 'inventory.add_worker'
    WORKERS_DETAILS = 'inventory.worker_details'
    
    # Quick Scan
    QUICK_SCAN = 'quick_scan.index'
    
    # API
    API_SCAN = 'api.scan'
    
    @classmethod
    def get_all_routes(cls):
        """Gibt alle definierten Routen zurück"""
        return {name: getattr(cls, name) 
                for name in dir(cls) 
                if not name.startswith('_') and isinstance(getattr(cls, name), str)} 