# backend/Dockerfile
FROM python:3.11-alpine
WORKDIR /app

# --- START OF FIX ---
# Install build dependencies, including the Rust compiler, and then postgresql-client
RUN apk add --no-cache cargo rust postgresql-client netcat-openbsd graphviz graphviz-dev

# --- END OF FIX ---

ENV PYTHONPATH /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Ensure the entrypoint script is executable
RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 5000

# Set the entrypoint
ENTRYPOINT ["/app/backend/entrypoint.sh"]