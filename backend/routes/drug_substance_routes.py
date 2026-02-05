# backend/routes/drug_substance_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from ..services import drug_substance_service
from ..models import DrugSubstance

drug_substance_routes = Blueprint(
    'drug_substances',
    __name__,
    url_prefix='/drug-substances'
)

drug_substance_api_bp = Blueprint(
    'drug_substance_api',
    __name__,
    url_prefix='/api/drug-substances'
)


# ============================================================================
# WEB ROUTES
# ============================================================================

@drug_substance_routes.route('/')
@login_required
def list_drug_substances():
    """List all drug substances with dynamic column selection."""
    requested_columns = request.args.get('columns')
    context = drug_substance_service.get_drug_substance_table_context(requested_columns)
    return render_template('drug_substances/list.html', title="Drug Substances", **context)


@drug_substance_routes.route('/<int:ds_id>')
@login_required
def view_drug_substance(ds_id):
    """View single drug substance detail page."""
    ds = drug_substance_service.get_drug_substance_by_id(ds_id)
    if not ds:
        return render_template('errors/404.html', message="Drug Substance not found"), 404
    return render_template('drug_substances/detail.html', title=ds.code, drug_substance=ds)


# ============================================================================
# API ROUTES
# ============================================================================

@drug_substance_api_bp.route('/', methods=['GET'])
@login_required
def api_list_drug_substances():
    """API: List all drug substances."""
    drug_substances = drug_substance_service.get_all_drug_substances()
    return jsonify([{
        'id': ds.id,
        'code': ds.code,
        'inn': ds.inn,
        'molecule_type': ds.molecule_type,
        'status': ds.status,
        'demand_category': ds.demand_category,
        'modality_name': ds.modality.modality_name if ds.modality else None,
        'project_count': len(ds.projects),
        'drug_product_count': len(ds.drug_products)
    } for ds in drug_substances])


@drug_substance_api_bp.route('/<int:ds_id>', methods=['GET'])
@login_required
def api_get_drug_substance(ds_id):
    """API: Get single drug substance."""
    ds = drug_substance_service.get_drug_substance_by_id(ds_id)
    if not ds:
        return jsonify(success=False, message="Drug Substance not found"), 404

    return jsonify({
        'id': ds.id,
        'code': ds.code,
        'inn': ds.inn,
        'molecule_type': ds.molecule_type,
        'mechanism_of_action': ds.mechanism_of_action,
        'technology': ds.technology,
        'storage_conditions': ds.storage_conditions,
        'shelf_life': ds.shelf_life,
        'development_approach': ds.development_approach,
        'development_site': ds.development_site,
        'launch_site': ds.launch_site,
        'release_site': ds.release_site,
        'routine_site': ds.routine_site,
        'demand_category': ds.demand_category,
        'demand_launch_year': ds.demand_launch_year,
        'demand_peak_year': ds.demand_peak_year,
        'peak_demand_range': ds.peak_demand_range,
        'commercial': ds.commercial,
        'status': ds.status,
        'type': ds.type,
        'biel': ds.biel,
        'd_and_dl_ops': ds.d_and_dl_ops,
        'last_refresh': ds.last_refresh.isoformat() if ds.last_refresh else None,
        'modality': {
            'id': ds.modality.modality_id,
            'name': ds.modality.modality_name
        } if ds.modality else None,
        'projects': [{'id': p.id, 'name': p.name} for p in ds.projects],
        'drug_products': [{'id': dp.id, 'code': dp.code} for dp in ds.drug_products]
    })


@drug_substance_api_bp.route('/', methods=['POST'])
@login_required
def api_create_drug_substance():
    """API: Create new drug substance."""
    data = request.json
    if not data or not data.get('code'):
        return jsonify(success=False, message="Code is required"), 400

    # Check for duplicate
    existing = drug_substance_service.get_drug_substance_by_code(data['code'])
    if existing:
        return jsonify(success=False, message=f"Code '{data['code']}' already exists"), 400

    ds = drug_substance_service.create_drug_substance(data)
    return jsonify(success=True, id=ds.id, message="Drug Substance created"), 201


@drug_substance_api_bp.route('/<int:ds_id>', methods=['PUT'])
@login_required
def api_update_drug_substance(ds_id):
    """API: Update drug substance (full or partial)."""
    data = request.json
    if not data:
        return jsonify(success=False, message="No data provided"), 400

    ds = DrugSubstance.query.get(ds_id)
    if not ds:
        return jsonify(success=False, message="Drug Substance not found"), 404

    for field, value in data.items():
        if hasattr(ds, field) and field not in ['id', 'created_at']:
            setattr(ds, field, value)

    from ..db import db
    db.session.commit()
    return jsonify(success=True, message="Drug Substance updated")


@drug_substance_api_bp.route('/<int:ds_id>/inline-update', methods=['PUT'])
@login_required
def api_inline_update_drug_substance(ds_id):
    """API: Inline update single field."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data"), 400

    field, value = list(data.items())[0]
    ds, message = drug_substance_service.inline_update_drug_substance_field(ds_id, field, value)

    if not ds:
        return jsonify(success=False, message=message), 400
    return jsonify(success=True, message=message)


@drug_substance_api_bp.route('/<int:ds_id>', methods=['DELETE'])
@login_required
def api_delete_drug_substance(ds_id):
    """API: Delete drug substance."""
    success, message = drug_substance_service.delete_drug_substance(ds_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)
