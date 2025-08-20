# backend/db.py

from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# No longer need to import Base here
# from .models import Base 

db = SQLAlchemy()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False))
migrate = Migrate()

def init_app_db(app):
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        SessionLocal.configure(bind=db.engine)
        # The problematic reflection call has been removed.
        print("Database engine configured. Alembic will manage schema migrations.")

    # Return both db and migrate instances
    return db, migrate