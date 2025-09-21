# backend/routes/process_stage_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import process_stage_service

process_stage_routes = Blueprint('process_stages', __name__, url_prefix='/process-stages')

@process_stage_routes.route('/')
@login_required
def list_process_stages():
    """Display all process stages in a table view."""
    requested_columns = request.args.get('columns')
    context = process_stage_service.get_process_stage_table_context(requested_columns)
    return render_template(
        'process_stages.html',
        title="Process Stages",
        **context
    )

@process_stage_routes.route('/hierarchy')
@login_required
def view_hierarchy():
    """Display process stages in a hierarchical tree view."""
    hierarchical_data = process_stage_service.get_hierarchical_stages()
    return render_template(
        'process_stages_hierarchy.html',
        title="Process Stage Hierarchy",
        stages=hierarchical_data
    )

@process_stage_routes.route('/api/process-stages/<int:stage_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_stage(stage_id):
    """API endpoint for inline editing of process stage fields."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    stage, message = process_stage_service.inline_update_stage_field(
        stage_id, field, value
    )

    if not stage:
        return jsonify(success=False, message=message), 400

    # Return the updated object
    updated_data = {
        f.key: getattr(stage, f.key) for f in stage.__class__.get_all_fields()
    }

    return jsonify(success=True, message=message, process_stage=updated_data)