# backend/routes/project_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from ..services import project_service
from ..models import Project, DrugSubstance, DrugProduct

project_routes = Blueprint(
    'projects',
    __name__,
    url_prefix='/projects'
)

project_api_bp = Blueprint(
    'project_api',
    __name__,
    url_prefix='/api/projects'
)


# ============================================================================
# WEB ROUTES
# ============================================================================

@project_routes.route('/')
@login_required
def list_projects():
    """List all projects with dynamic column selection."""
    requested_columns = request.args.get('columns')
    context = project_service.get_project_table_context(requested_columns)
    return render_template('projects/list.html', title="Projects", **context)


@project_routes.route('/<int:project_id>')
@login_required
def view_project(project_id):
    """View single project detail page."""
    project = project_service.get_project_by_id(project_id)
    if not project:
        return render_template('errors/404.html', message="Project not found"), 404

    # Get all drug substances and products for linking dropdowns
    all_drug_substances = DrugSubstance.query.order_by(DrugSubstance.code).all()
    all_drug_products = DrugProduct.query.order_by(DrugProduct.code).all()

    return render_template('projects/detail.html',
        title=project.name,
        project=project,
        all_drug_substances=all_drug_substances,
        all_drug_products=all_drug_products
    )


@project_routes.route('/timeline')
@login_required
def project_timeline():
    """View project timeline (Gantt chart style)."""
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    timeline_data = project_service.get_timeline_overview(start_year, end_year)
    return render_template('projects/timeline.html', title="Project Timeline", timeline_data=timeline_data)


# ============================================================================
# API ROUTES
# ============================================================================

@project_api_bp.route('/', methods=['GET'])
@login_required
def api_list_projects():
    """API: List all projects."""
    projects = project_service.get_all_projects()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'indication': p.indication,
        'project_type': p.project_type,
        'administration': p.administration,
        'launch': p.launch.isoformat() if p.launch else None,
        'drug_substance_count': len(p.drug_substances),
        'drug_product_count': len(p.drug_products)
    } for p in projects])


@project_api_bp.route('/<int:project_id>', methods=['GET'])
@login_required
def api_get_project(project_id):
    """API: Get single project with full details."""
    project = project_service.get_project_by_id(project_id)
    if not project:
        return jsonify(success=False, message="Project not found"), 404

    return jsonify({
        'id': project.id,
        'name': project.name,
        'indication': project.indication,
        'project_type': project.project_type,
        'administration': project.administration,
        'timeline': project.get_timeline_dict(),
        'drug_substances': [{
            'id': ds.id,
            'code': ds.code,
            'inn': ds.inn,
            'molecule_type': ds.molecule_type,
            'modality': ds.modality.modality_name if ds.modality else None
        } for ds in project.drug_substances],
        'drug_products': [{
            'id': dp.id,
            'code': dp.code,
            'pharm_form': dp.pharm_form,
            'classification': dp.classification
        } for dp in project.drug_products]
    })


@project_api_bp.route('/', methods=['POST'])
@login_required
def api_create_project():
    """API: Create new project."""
    data = request.json
    if not data or not data.get('name'):
        return jsonify(success=False, message="Name is required"), 400

    # Check for duplicate
    existing = project_service.get_project_by_name(data['name'])
    if existing:
        return jsonify(success=False, message=f"Project '{data['name']}' already exists"), 400

    project = project_service.create_project(data)
    return jsonify(success=True, id=project.id, message="Project created"), 201


@project_api_bp.route('/<int:project_id>', methods=['PUT'])
@login_required
def api_update_project(project_id):
    """API: Update project (full or partial)."""
    data = request.json
    if not data:
        return jsonify(success=False, message="No data provided"), 400

    project = Project.query.get(project_id)
    if not project:
        return jsonify(success=False, message="Project not found"), 404

    from datetime import datetime
    date_fields = ['sod', 'dsmm3', 'dsmm4', 'dpmm3', 'dpmm4', 'rofd', 'submission', 'launch']

    for field, value in data.items():
        if hasattr(project, field) and field not in ['id', 'created_at']:
            if field in date_fields and value:
                if isinstance(value, str):
                    value = datetime.strptime(value, '%Y-%m-%d').date()
            setattr(project, field, value)

    from ..db import db
    db.session.commit()
    return jsonify(success=True, message="Project updated")


@project_api_bp.route('/<int:project_id>/inline-update', methods=['PUT'])
@login_required
def api_inline_update_project(project_id):
    """API: Inline update single field."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data"), 400

    field, value = list(data.items())[0]
    project, message = project_service.inline_update_project_field(project_id, field, value)

    if not project:
        return jsonify(success=False, message=message), 400
    return jsonify(success=True, message=message)


@project_api_bp.route('/<int:project_id>', methods=['DELETE'])
@login_required
def api_delete_project(project_id):
    """API: Delete project."""
    success, message = project_service.delete_project(project_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)


# ============================================================================
# LINK MANAGEMENT ROUTES
# ============================================================================

@project_api_bp.route('/<int:project_id>/link-drug-substance/<int:ds_id>', methods=['POST'])
@login_required
def api_link_drug_substance(project_id, ds_id):
    """API: Link a drug substance to this project."""
    success, message = project_service.link_drug_substance(project_id, ds_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)


@project_api_bp.route('/<int:project_id>/unlink-drug-substance/<int:ds_id>', methods=['DELETE'])
@login_required
def api_unlink_drug_substance(project_id, ds_id):
    """API: Unlink a drug substance from this project."""
    success, message = project_service.unlink_drug_substance(project_id, ds_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)


@project_api_bp.route('/<int:project_id>/link-drug-product/<int:dp_id>', methods=['POST'])
@login_required
def api_link_drug_product(project_id, dp_id):
    """API: Link a drug product to this project."""
    success, message = project_service.link_drug_product(project_id, dp_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)


@project_api_bp.route('/<int:project_id>/unlink-drug-product/<int:dp_id>', methods=['DELETE'])
@login_required
def api_unlink_drug_product(project_id, dp_id):
    """API: Unlink a drug product from this project."""
    success, message = project_service.unlink_drug_product(project_id, dp_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)


# ============================================================================
# TIMELINE & ANALYTICS ROUTES
# ============================================================================

@project_api_bp.route('/timeline', methods=['GET'])
@login_required
def api_timeline_overview():
    """API: Get timeline data for all projects (for Gantt chart)."""
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    timeline_data = project_service.get_timeline_overview(start_year, end_year)
    return jsonify(timeline_data)


@project_api_bp.route('/by-launch-year/<int:year>', methods=['GET'])
@login_required
def api_projects_by_launch_year(year):
    """API: Get all projects launching in a specific year."""
    projects = project_service.get_projects_by_launch_year(year)
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'indication': p.indication,
        'launch': p.launch.isoformat() if p.launch else None
    } for p in projects])


@project_api_bp.route('/by-indication/<indication>', methods=['GET'])
@login_required
def api_projects_by_indication(indication):
    """API: Get all projects for a specific indication."""
    projects = project_service.get_projects_by_indication(indication)
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'project_type': p.project_type,
        'launch': p.launch.isoformat() if p.launch else None
    } for p in projects])
