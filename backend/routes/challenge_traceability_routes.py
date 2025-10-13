# /backend/routes/challenge_traceability_routes.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import challenge_traceability_service as service
from ..models import Modality, ProcessTemplate, ProcessStage, ManufacturingTechnology, ManufacturingChallenge

challenge_traceability_bp = Blueprint('challenge_traceability', __name__,
                                      url_prefix='/challenge-traceability')


@challenge_traceability_bp.route('/')
@login_required
def explorer_page():
    """Renders the main Challenge Traceability Explorer page."""
    return render_template('challenge_traceability_explorer.html')


@challenge_traceability_bp.route('/api/data')
@login_required
def get_traceability_data_api():
    """API endpoint for fetching traceability data."""
    modality_id = request.args.get('modality_id', type=int)
    template_id = request.args.get('template_id', type=int)
    challenge_id = request.args.get('challenge_id', type=int)

    data = service.get_traceability_data(
        modality_id, template_id, challenge_id)
    return jsonify(data)


@challenge_traceability_bp.route('/api/filters')
@login_required
def get_filter_options():
    """Returns all available filter options."""
    filters = service.get_available_filters()
    return jsonify(filters)


@challenge_traceability_bp.route('/api/templates-by-modality/<int:modality_id>')
@login_required
def get_templates_by_modality_api(modality_id):
    """Returns templates filtered by modality for cascade filtering."""
    templates = service.get_templates_by_modality(modality_id)
    return jsonify(templates)


@challenge_traceability_bp.route('/api/node-details/<node_type>/<int:node_id>')
@login_required
def get_node_details(node_type, node_id):
    """Returns detailed information for a specific node."""
    details = {}
    if node_type == 'modality':
        node = Modality.query.get(node_id)
        if node:
            details = {
                "category": node.modality_category,
                "template_count": len(node.process_templates),
                "description": node.description
            }
    elif node_type == 'template':
        node = ProcessTemplate.query.get(node_id)
        if node:
            details = {
                "modality_name": node.modality.modality_name if node.modality else 'N/A',
                "stage_count": len(node.stages)
            }
    elif node_type == 'challenge':
        node = ManufacturingChallenge.query.get(node_id)
        if node:
            details = {
                "category": node.challenge_category,
                "severity_level": node.severity_level,
                "product_count": len(node.products)
            }
    # Add other node types (Stage, Technology) as needed

    return jsonify(details)