#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be ready.
# We will try to connect to the database in a loop until it's successful.
echo "Waiting for database to be ready..."
# The 'postgres' database is always created by default, so we connect to it
# to check if the server is fully up and accepting commands.
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "$POSTGRES_USER" -d "postgres" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up and running"

# Now that we know the server is up, we can safely run the migrations.
# The Flask application will connect to the 'asset_tracker_db'.
echo "Running database migrations..."
flask db upgrade

# Start the main application.
echo "Starting Gunicorn server..."
exec gunicorn --workers 4 --bind 0.0.0.0:5000 "backend.app:create_app()"