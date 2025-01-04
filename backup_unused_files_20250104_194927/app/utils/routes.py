class Routes:
    """Zentrale Klasse für alle Routen-Konstanten"""
    
    # Auth Routes
    LOGIN = 'auth.login'
    LOGOUT = 'auth.logout'
    
    # Tool Routes
    TOOLS_INDEX = 'tools.index'
    ADD_TOOL = 'tools.add'
    TOOL_DETAILS = 'tools.details'
    EDIT_TOOL = 'tools.edit'
    DELETE_TOOL = 'tools.delete'
    
    # Worker Routes
    WORKERS_INDEX = 'workers.index'
    ADD_WORKER = 'workers.add'
    WORKER_DETAILS = 'workers.details'
    EDIT_WORKER = 'workers.edit'
    DELETE_WORKER = 'workers.delete'
    
    # Consumable Routes
    CONSUMABLES_INDEX = 'consumables.index'
    ADD_CONSUMABLE = 'consumables.add'
    CONSUMABLE_DETAILS = 'consumables.details'
    EDIT_CONSUMABLE = 'consumables.edit'
    DELETE_CONSUMABLE = 'consumables.delete'
    
    # Admin Routes
    ADMIN_DASHBOARD = 'admin.dashboard'
    ADMIN_MANUAL_LENDING = 'admin.manual_lending'
    
    # Inventory Routes
    INVENTORY_TOOLS = 'inventory.tools'
    INVENTORY_WORKERS = 'inventory.workers'
    INVENTORY_CONSUMABLES = 'inventory.consumables'
    
    # Quick Scan Route
    QUICK_SCAN = 'quick_scan.quick_scan'
    
    # History Route
    HISTORY = 'history.view_history'
    
    @classmethod
    def get_all_routes(cls):
        """Gibt alle definierten Routen zurück"""
        return {name: getattr(cls, name) 
                for name in dir(cls) 
                if not name.startswith('_') and isinstance(getattr(cls, name), str)} 