# backend/routes/process_stage_routes.py
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required
from ..services import process_stage_service
import json # Import json for the export

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


@process_stage_routes.route('/<int:stage_id>')
@login_required
def view_stage_detail(stage_id):
    """Display the new detail page for a single process stage."""
    details = process_stage_service.get_stage_details(stage_id)
    if not details:
        flash("Process Stage not found.", "danger")
        return redirect(url_for('process_stages.list_process_stages'))
    
    return render_template(
        'process_stage_detail.html', 
        title=f"Stage: {details['stage'].stage_name}",
        stage=details['stage'],
        challenges=details['challenges']
    )

@process_stage_routes.route('/<int:stage_id>/export-challenges')
@login_required
def export_stage_challenges(stage_id):
    """Export the challenges linked to this stage as JSON."""
    details = process_stage_service.get_stage_details(stage_id)
    if not details:
        return jsonify({"error": "Stage not found"}), 404
        
    export_data = {
        "process_stage": {
            "id": details['stage'].stage_id,
            "name": details['stage'].stage_name,
            "category": details['stage'].stage_category
        },
        "associated_challenges": [
            {
                "id": c.challenge_id,
                "name": c.challenge_name,
                "category": c.challenge_category,
                "severity": c.severity_level
            } for c in details['challenges']
        ]
    }
    
    filename = f"stage_{details['stage'].stage_name}_challenges.json"
    return Response(
        json.dumps(export_data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@process_stage_routes.route('/api/process-stages/<int:stage_id>/update-challenges', methods=['POST'])
@login_required
def api_update_stage_challenges(stage_id):
    """API endpoint to update challenge associations for a stage."""
    data = request.json
    challenge_ids = data.get('challenge_ids', [])
    
    if not isinstance(challenge_ids, list):
        return jsonify(success=False, message="Invalid data format: challenge_ids must be a list."), 400
        
    success, message = process_stage_service.update_stage_challenges(stage_id, challenge_ids)
    
    if success:
        return jsonify(success=True, message=message)
    else:
        return jsonify(success=False, message=message), 500
    


@process_stage_routes.route('/challenge-map')
@login_required
def view_hierarchy_with_challenges():
    """Display the new, enhanced hierarchy view with challenges."""
    hierarchical_data = process_stage_service.get_hierarchical_stages_with_challenges()
    return render_template(
        'process_stage_challenges_overview.html',
        title="Challenge Mapping Overview",
        stages_with_challenges=hierarchical_data
    )