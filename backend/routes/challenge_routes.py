from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import challenge_service
from ..models import Challenge

# Blueprint for web pages
challenge_routes = Blueprint('challenges', __name__, url_prefix='/challenges')

# Blueprint for challenge-related APIs
challenge_api_bp = Blueprint('challenge_api', __name__, url_prefix='/api/challenges')


# --- Web Page Route ---

@challenge_routes.route('/')
@login_required
def list_challenges():
    requested_columns = request.args.get('columns')
    context = challenge_service.get_challenge_table_context(requested_columns)
    return render_template(
        'manufacturing_challenges.html',
        title="Challenges",
        **context
    )


# --- API Routes ---

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

    return jsonify(success=True, message=message)


@challenge_api_bp.route('/available')
@login_required
def get_available_challenges():
    """Get all available challenges."""
    challenges = Challenge.query.order_by(Challenge.name).all()

    return jsonify([
        {
            'id': c.id,
            'name': c.name,
            'value_step': c.value_step,
            'agnostic_description': c.agnostic_description
        } for c in challenges
    ])


@challenge_api_bp.route('/all')
@login_required
def get_all_challenges_for_linking():
    """Get a simple list of all challenges for UI selectors."""
    all_challenges = challenge_service.get_all_challenges()
    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "value_step": c.value_step
        } for c in all_challenges
    ])


@challenge_api_bp.route('/<int:challenge_id>/modality-details')
@login_required
def get_challenge_modality_details(challenge_id):
    """Get all modality-specific details for a challenge."""
    result = challenge_service.get_challenge_with_modality_details(challenge_id)
    if not result:
        return jsonify(success=False, message="Challenge not found"), 404

    return jsonify({
        'challenge': {
            'id': result['challenge'].id,
            'name': result['challenge'].name,
            'agnostic_description': result['challenge'].agnostic_description,
            'agnostic_root_cause': result['challenge'].agnostic_root_cause,
            'value_step': result['challenge'].value_step
        },
        'modality_details': [
            {
                'id': d.id,
                'modality_id': d.modality_id,
                'modality_name': d.modality.modality_name if d.modality else None,
                'specific_description': d.specific_description,
                'specific_root_cause': d.specific_root_cause,
                'impact_score': d.impact_score,
                'impact_details': d.impact_details,
                'maturity_score': d.maturity_score,
                'maturity_details': d.maturity_details,
                'trends_3_5_years': d.trends_3_5_years
            } for d in result['modality_details']
        ]
    })
