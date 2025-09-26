# migrations/env.py - FIXED VERSION

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
#if config.config_file_name is not None:
#    fileConfig(config.config_file_name)

# CHANGE THIS: Instead of importing Base, import db
from backend.app import create_app
from backend.db import db

# THIS IS THE KEY CHANGE: Call create_app with the new flag
app = create_app(init_session=False)  

# CHANGE THIS: Use db.metadata instead of Base.metadata
target_metadata = db.metadata

# Exclude specific tables AND views from Alembic migrations
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in ["flask_sessions", "all_product_requirements", "product_complexity_summary"]:
        return False
    else:
        return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # We wrap the code that needs the Flask app in an app_context.
    with app.app_context():
        connectable = app.extensions['sqlalchemy'].engine

        with connectable.connect() as connection:
            context.configure(
                connection=connection, 
                target_metadata=target_metadata,
                include_object=include_object,
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()