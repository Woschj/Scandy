from flask import Flask
from flask_login import LoginManager
from .models.user import User
from .utils.routes import Routes
from .routes import index, inventory, admin, auth, api
from .models.database import Database
from .utils.url_config import get_urls
from .utils.db_schema import SchemaManager

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'  # Ändern Sie dies in der Produktion
    
    @app.context_processor
    def inject_routes():
        return {"routes": Routes}
    
    # Login Manager Setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    # Blueprints registrieren
    app.register_blueprint(index.bp)
    app.register_blueprint(inventory.bp, url_prefix='/inventory')
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(api.bp)

    @app.teardown_appcontext
    def close_db(error):
        Database.close_db()

    # Context Processor registrieren
    from app.utils.context_processors import inject_colors, inject_settings, inject_urls
    app.context_processor(inject_colors)
    app.context_processor(inject_settings)
    app.context_processor(inject_urls)

    # Schema beim Start generieren
    with app.app_context():
        SchemaManager.generate_schema()

    return app