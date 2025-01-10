from flask import Blueprint, render_template, current_app
from app.models.database import Database
from app.config import Config

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def index():
    db = Database()
    stats = {
        'total_tools': db.get_total_tools(),
        'available_tools': db.get_available_tools(),
        'total_workers': db.get_total_workers(),
        'active_lendings': db.get_active_lendings()
    }
    
    settings = {
        'server_mode': db.get_setting('server_mode'),
        'server_url': db.get_setting('server_url'),
        'client_name': db.get_setting('client_name'),
        'auto_sync': db.get_setting('auto_sync')
    }
    
    # Hole Sync-Logs nur im Server-Modus
    sync_logs = db.get_sync_logs() if Config.SERVER_MODE else []
    last_sync = db.get_last_sync_time()
    
    return render_template('dashboard.html',
                         stats=stats,
                         settings=settings,
                         sync_logs=sync_logs,
                         last_sync=last_sync,
                         config=Config) 