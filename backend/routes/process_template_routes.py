# backend/routes/process_template_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import process_template_service

process_template_routes = Blueprint('process_templates', __name__, url_prefix='/process-templates')

@process_template_routes.route('/')
@login_required
def list_process_templates():
    """Display all process templates in a table view."""
    requested_columns = request.args.get('columns')
    context = process_template_service.get_process_template_table_context(requested_columns)
    return render_template(
        'process_templates.html',
        title="Process Templates",
        **context
    )

@process_template_routes.route('/<int:template_id>')
@login_required
def view_template_detail(template_id):
    """Display detailed view of a specific process template with its stages."""
    template_data = process_template_service.get_template_with_stages(template_id)
    
    if not template_data:
        flash('Process template not found.', 'error')
        return redirect(url_for('process_templates.list_process_templates'))
    
    return render_template(
        'process_template_detail.html',
        title=f"Template: {template_data['template'].template_name}",
        template_data=template_data
    )

@process_template_routes.route('/api/process-templates/<int:template_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_template(template_id):
    """API endpoint for inline editing of process template fields."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    template, message = process_template_service.inline_update_template_field(
        template_id, field, value
    )

    if not template:
        return jsonify(success=False, message=message), 400

    # Return the updated object
    updated_data = {
        'template_id': template.template_id,
        'template_name': template.template_name,
        'description': template.description,
        'modality_name': template.modality.modality_name if template.modality else None,
        'created_at': template.created_at.isoformat() if template.created_at else None,
        'stage_count': len(template.stages)
    }

    return jsonify(success=True, message=message, process_template=updated_data)