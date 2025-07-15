# backend/app.py
import os
from flask import Flask, g, redirect, url_for
from flask_login import LoginManager
from flask_session import Session
from flask_assets import Environment
from flask_migrate import Migrate

from backend.config import get_config
from backend.models import User
from backend.db import db, init_app_db, SessionLocal
from backend.utils import nl2br, markdown_to_html_filter, truncate_filter
from backend.assets import js_main_bundle, css_bundle

# Import new blueprints
import backend.routes.auth_routes as auth_routes_mod
import backend.routes.settings_routes as settings_routes_mod
import backend.routes.api_routes as api_routes_mod
import backend.routes.product_routes as product_routes_mod
import backend.routes.indication_routes as indication_routes_mod
import backend.routes.challenge_routes as challenge_routes_mod
import backend.routes.technology_routes as technology_routes_mod
import backend.routes.partner_routes as partner_routes_mod
import backend.routes.data_management_routes as data_management_routes_mod


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    session = g.get('db_session', SessionLocal())
    try:
        return session.query(User).get(int(user_id))
    except (ValueError, TypeError):
        return None
    finally:
        if 'db_session' not in g:
            SessionLocal.remove()

# --- THIS IS THE KEY CORRECTION ---
# The function now accepts the 'init_session' argument
def create_app(init_session=True):
    app = Flask(__name__, instance_relative_config=True, static_folder='static', template_folder='templates')

    app.config.from_object(get_config())
    
    # Initialize extensions
    init_app_db(app)
    login_manager.init_app(app)

    assets = Environment(app)
    assets.register('js_main', js_main_bundle)
    assets.register('css_main', css_bundle)
    assets.url = app.static_url_path

    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.filters['markdown'] = markdown_to_html_filter
    app.jinja_env.filters['truncate'] = truncate_filter

    # Use the parameter to decide whether to initialize Flask-Session
    if init_session:
        app.config['SESSION_TYPE'] = 'sqlalchemy'
        app.config['SESSION_SQLALCHEMY_TABLE'] = 'flask_sessions'
        app.config['SESSION_SQLALCHEMY'] = db
        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 7
        Session(app)

    @app.before_request
    def before_request():
        g.db_session = SessionLocal()

    @app.teardown_appcontext
    def teardown_appcontext(exception=None):
        db_session = g.pop('db_session', None)
        if db_session is not None:
            SessionLocal.remove()

    # Register blueprints
    app.register_blueprint(auth_routes_mod.auth_routes)
    app.register_blueprint(settings_routes_mod.settings_routes)
    app.register_blueprint(api_routes_mod.api_bp)
    app.register_blueprint(product_routes_mod.product_routes)
    app.register_blueprint(indication_routes_mod.indication_routes)
    app.register_blueprint(challenge_routes_mod.challenge_routes)
    app.register_blueprint(technology_routes_mod.technology_routes)
    app.register_blueprint(partner_routes_mod.partner_routes)
    app.register_blueprint(data_management_routes_mod.data_management_bp)


    @app.route('/')
    def index():
        return redirect(url_for('products.list_products'))

    return app