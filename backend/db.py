# backend/db.py - SIMPLIFIED VERSION
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Just use Flask-SQLAlchemy - it handles sessions automatically
db = SQLAlchemy()
migrate = Migrate()

def init_app_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        print("Database configured with Flask-SQLAlchemy")
    
    return db, migrate