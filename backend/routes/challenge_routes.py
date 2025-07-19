# backend/routes/challenge_routes.py
from flask import Blueprint, render_template, request, g, jsonify
from flask_login import login_required
from ..services import challenge_service

challenge_routes = Blueprint('challenges', __name__, url_prefix='/challenges')

@challenge_routes.route('/')
@login_required
def list_challenges():
    requested_columns = request.args.get('columns')
    context = challenge_service.get_challenge_table_context(g.db_session, requested_columns)
    return render_template('manufacturing_challenges.html', title="Manufacturing Challenges", **context)

@challenge_routes.route('/api/challenges/<int:challenge_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_challenge(challenge_id):
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400
    
    field, value = list(data.items())[0]
    
    challenge, message = challenge_service.inline_update_challenge_field(g.db_session, challenge_id, field, value)

    if not challenge:
        return jsonify(success=False, message=message), 400
        
    # Return the updated object so the frontend can display it if needed
    updated_data = {f.key: getattr(challenge, f.key) for f in challenge.__class__.get_all_fields()}
        
    return jsonify(success=True, message=message, challenge=updated_data)