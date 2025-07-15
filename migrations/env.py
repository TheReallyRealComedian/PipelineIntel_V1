# C:\Users\glutholi\CODE\UsecaseExplorer\migrations\env.py

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

# add your model's MetaData object here
# for 'autogenerate' support
from backend.models import Base
from backend.app import create_app

# THIS IS THE KEY CHANGE: Call create_app with the new flag
app = create_app(init_session=False)  
target_metadata = Base.metadata

# Exclude specific tables from Alembic migrations
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name == "flask_sessions":
        return False
    else:
        return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    # ... (rest of the function is correct) ...
    """
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
    # --- START MODIFICATION ---
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
    # --- END MODIFICATION ---


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()