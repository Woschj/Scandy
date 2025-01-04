def get_urls():
    """Zentrale URL-Konfiguration"""
    return {
        # Admin URLs
        'add_worker': 'admin.add_worker',
        'add_tool': 'admin.add_tool',
        'add_consumable': 'admin.add_consumable',
        'manual_lending': 'admin.manual_lending',
        'dashboard': 'admin.dashboard',
        
        # Inventory URLs
        'workers': 'inventory.workers',
        'tools': 'inventory.tools',
        'consumables': 'inventory.consumables',
        'worker_details': 'inventory.worker_details',
        'tool_details': 'inventory.tool_details',
        'consumable_details': 'inventory.consumable_details',
        'edit_tool': 'inventory.update_tool',
    } 