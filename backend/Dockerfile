# backend/Dockerfile
FROM python:3.11-alpine
WORKDIR /app

# Install postgresql-client for psql and netcat-openbsd for the old wait method
RUN apk add --no-cache postgresql-client netcat-openbsd

ENV PYTHONPATH /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Ensure the entrypoint script is executable
RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 5000

# Set the entrypoint
ENTRYPOINT ["/app/backend/entrypoint.sh"]