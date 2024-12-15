# app/routes/__init__.py
from flask import Flask
from app.routes import (
    admin,
    api,
    auth,
    consumables,
    history,
    index,
    tools,
    workers,
    quick_scan
)

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(consumables.bp)
    app.register_blueprint(history.bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(workers.bp)
    app.register_blueprint(quick_scan.bp)
    
    return app