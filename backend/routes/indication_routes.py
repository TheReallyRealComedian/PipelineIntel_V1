# backend/routes/indication_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import indication_service

indication_routes = Blueprint('indications', __name__, url_prefix='/indications')

@indication_routes.route('/')
@login_required
def list_indications():
    requested_columns = request.args.get('columns')
    context = indication_service.get_indication_table_context(requested_columns)
    return render_template(
        'indications.html',
        title="Clinical Indications",
        **context
    )

@indication_routes.route('/api/indications/<int:indication_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_indication(indication_id):
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    indication, message = indication_service.inline_update_indication_field(
        indication_id, field, value
    )

    if not indication:
        return jsonify(success=False, message=message), 400

    return jsonify(success=True, message=message)