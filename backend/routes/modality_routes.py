# backend/routes/modality_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from ..services import modality_service

modality_routes = Blueprint(
    'modalities',
    __name__,
    url_prefix='/modalities'
)


@modality_routes.route('/')
@login_required
def list_modalities():
    requested_columns = request.args.get('columns')
    context = modality_service.get_modality_table_context(requested_columns)
    return render_template('modalities.html', title="Modalities", **context)


@modality_routes.route('/api/modalities/<int:modality_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_modality(modality_id):
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    modality, message = modality_service.inline_update_modality_field(
        modality_id, field, value
    )

    if not modality:
        return jsonify(success=False, message=message), 400

    return jsonify(success=True, message=message)


@modality_routes.route('/complexity-analysis')
@login_required
def modality_complexity_analysis():
    # This is a placeholder for a future strategic analytics page
    # It will use modality_service.get_modality_complexity_analysis()
    return render_template(
        'analytics/placeholder.html',
        title="Modality Complexity Analysis",
        message="This page will contain a detailed analysis of manufacturing complexity driven by different modalities."
    )