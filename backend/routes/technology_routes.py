# backend/routes/technology_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import technology_service

technology_routes = Blueprint('technologies', __name__, url_prefix='/technologies')

@technology_routes.route('/')
@login_required
def list_technologies():
    requested_columns = request.args.get('columns')
    context = technology_service.get_technology_table_context(requested_columns)
    return render_template(
        'manufacturing_technologies.html',
        title="Manufacturing Technologies",
        **context
    )

@technology_routes.route('/api/technologies/<int:technology_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_technology(technology_id):
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    technology, message = technology_service.inline_update_technology_field(
        technology_id, field, value
    )

    if not technology:
        return jsonify(success=False, message=message), 400

    return jsonify(success=True, message=message)