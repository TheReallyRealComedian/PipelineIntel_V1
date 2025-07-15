# backend/routes/__init__.py
# This file is intentionally left minimal.
# Blueprint objects (e.g., for areas, steps, usecases, etc.)
# are now defined in their respective modules within the 'routes' package
# (e.g., backend/routes/area_routes.py, backend/routes/step_routes.py)
# and are imported directly into app.py for registration.

# For example:
# from .area_routes import area_routes
# from .step_routes import step_routes
# ... and so on, would be found in app.py or the main application factory.