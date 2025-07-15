# backend/routes/api_routes.py
from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health')
def health_check():
    """A simple health check endpoint for the API."""
    return jsonify({"status": "ok"}), 200

# You can add new API endpoints here later.