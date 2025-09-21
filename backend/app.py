import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_session import Session
from flask_assets import Environment
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect  # ADD THIS IMPORT

from backend.config import get_config
from backend.models import User
from backend.db import db, init_app_db
from backend.utils import nl2br, markdown_to_html_filter, truncate_filter
from backend.assets import js_main_bundle, css_bundle

# Import blueprints (unchanged)
import backend.routes.auth_routes as auth_routes_mod
import backend.routes.settings_routes as settings_routes_mod
import backend.routes.api_routes as api_routes_mod
import backend.routes.product_routes as product_routes_mod
import backend.routes.indication_routes as indication_routes_mod
import backend.routes.challenge_routes as challenge_routes_mod
import backend.routes.technology_routes as technology_routes_mod
import backend.routes.data_management_routes as data_management_routes_mod
import backend.routes.export_routes as export_routes_mod
import backend.routes.modality_routes as modality_routes_mod
import backend.routes.facility_routes as facility_routes_mod
import backend.routes.analytics_routes as analytics_routes_mod
import backend.routes.process_stage_routes as process_stage_routes_mod

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user - now using db.session directly."""
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

def create_app(init_session=True):
    app = Flask(__name__, instance_relative_config=True, static_folder='static', template_folder='templates')
    app.config.from_object(get_config())
    
    # Initialize extensions
    init_app_db(app)
    login_manager.init_app(app)
    
    # ADD THIS: Initialize CSRF protection
    csrf = CSRFProtect(app)

    assets = Environment(app)
    assets.register('js_main', js_main_bundle)
    assets.register('css_main', css_bundle)
    assets.url = app.static_url_path

    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.filters['markdown'] = markdown_to_html_filter
    app.jinja_env.filters['truncate'] = truncate_filter

    if init_session:
        app.config['SESSION_TYPE'] = 'sqlalchemy'
        app.config['SESSION_SQLALCHEMY_TABLE'] = 'flask_sessions'
        app.config['SESSION_SQLALCHEMY'] = db
        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 7
        Session(app)

    # Register blueprints (unchanged)
    app.register_blueprint(auth_routes_mod.auth_routes)
    app.register_blueprint(settings_routes_mod.settings_routes)
    app.register_blueprint(api_routes_mod.api_bp)
    app.register_blueprint(product_routes_mod.product_routes)
    app.register_blueprint(indication_routes_mod.indication_routes)
    app.register_blueprint(challenge_routes_mod.challenge_routes)
    app.register_blueprint(technology_routes_mod.technology_routes)
    app.register_blueprint(data_management_routes_mod.data_management_bp)
    app.register_blueprint(export_routes_mod.export_bp)
    app.register_blueprint(modality_routes_mod.modality_routes)
    app.register_blueprint(facility_routes_mod.facility_routes)
    app.register_blueprint(analytics_routes_mod.analytics_routes)
    app.register_blueprint(process_stage_routes_mod.process_stage_routes)

    @app.route('/')
    def index():
        return redirect(url_for('products.list_products'))

    return app