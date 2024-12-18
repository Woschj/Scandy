# app/routes/__init__.py
from flask import Flask
from app.routes.auth import bp as auth_bp
from app.routes.tools import bp as tools_bp
from app.routes.workers import bp as workers_bp
from app.routes.consumables import bp as consumables_bp
from app.routes.api import bp as api_bp
from app.routes.admin import bp as admin_bp
from app.routes.inventory import bp as inventory_bp
from app.routes.quick_scan import bp as quick_scan_bp
from app.routes.history import bp as history_bp

__all__ = [
    'auth_bp', 'tools_bp', 'workers_bp', 'consumables_bp',
    'api_bp', 'admin_bp', 'inventory_bp', 'quick_scan_bp', 'history_bp'
]