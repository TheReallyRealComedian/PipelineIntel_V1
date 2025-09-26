from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import challenge_service
from ..models import ManufacturingChallenge # Import the model

# Blueprint for web pages
challenge_routes = Blueprint('challenges', __name__, url_prefix='/challenges')

# NEW: Blueprint specifically for challenge-related APIs
challenge_api_bp = Blueprint('challenge_api', __name__, url_prefix='/api/challenges')


# --- Web Page Route (Unchanged) ---

@challenge_routes.route('/')
@login_required
def list_challenges():
    requested_columns = request.args.get('columns')
    context = challenge_service.get_challenge_table_context(requested_columns)
    return render_template(
        'manufacturing_challenges.html',
        title="Manufacturing Challenges",
        **context
    )

# --- API Routes (Moved to the new blueprint with corrected paths) ---

@challenge_api_bp.route('/<int:challenge_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_challenge(challenge_id):
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    challenge, message = challenge_service.inline_update_challenge_field(
        challenge_id, field, value
    )

    if not challenge:
        return jsonify(success=False, message=message), 400

    updated_data = {
        f.key: getattr(challenge, f.key) for f in challenge.__class__.get_all_fields()
    }

    return jsonify(success=True, message=message, challenge=updated_data)

@challenge_api_bp.route('/available')
@login_required
def get_available_challenges():
    """Get all available challenges for adding to products."""
    challenges = ManufacturingChallenge.query.order_by(
        ManufacturingChallenge.challenge_category,
        ManufacturingChallenge.challenge_name
    ).all()

    return jsonify([
        {
            'challenge_id': c.challenge_id,
            'challenge_name': c.challenge_name,
            'challenge_category': c.challenge_category,
            'severity_level': c.severity_level,
            'short_description': c.short_description
        } for c in challenges
    ])