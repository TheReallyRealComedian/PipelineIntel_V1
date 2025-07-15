#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Entrypoint script started."

# The healthcheck in docker-compose ensures the DB is ready before this script runs.
# The 'Waiting for database...' message is for clarity.
echo "Database is ready."

echo "Running database migrations..."
flask db upgrade

echo "Starting Gunicorn server..."
# The 'exec' command replaces the shell process with the Gunicorn process.
exec gunicorn --workers 4 --bind 0.0.0.0:5000 "backend.app:create_app()"