# backend/routes/drug_product_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from ..services import drug_product_service
from ..models import DrugProduct

drug_product_routes = Blueprint(
    'drug_products',
    __name__,
    url_prefix='/drug-products'
)

drug_product_api_bp = Blueprint(
    'drug_product_api',
    __name__,
    url_prefix='/api/drug-products'
)


# ============================================================================
# WEB ROUTES
# ============================================================================

@drug_product_routes.route('/')
@login_required
def list_drug_products():
    """List all drug products with dynamic column selection."""
    requested_columns = request.args.get('columns')
    context = drug_product_service.get_drug_product_table_context(requested_columns)
    return render_template('drug_products/list.html', title="Drug Products", **context)


@drug_product_routes.route('/<int:dp_id>')
@login_required
def view_drug_product(dp_id):
    """View single drug product detail page."""
    dp = drug_product_service.get_drug_product_by_id(dp_id)
    if not dp:
        return render_template('errors/404.html', message="Drug Product not found"), 404
    return render_template('drug_products/detail.html', title=dp.code, drug_product=dp)


# ============================================================================
# API ROUTES
# ============================================================================

@drug_product_api_bp.route('/', methods=['GET'])
@login_required
def api_list_drug_products():
    """API: List all drug products."""
    drug_products = drug_product_service.get_all_drug_products()
    return jsonify([{
        'id': dp.id,
        'code': dp.code,
        'pharm_form': dp.pharm_form,
        'classification': dp.classification,
        'demand_category': dp.demand_category,
        'commercial': dp.commercial,
        'project_count': len(dp.projects),
        'drug_substance_count': len(dp.drug_substances)
    } for dp in drug_products])


@drug_product_api_bp.route('/<int:dp_id>', methods=['GET'])
@login_required
def api_get_drug_product(dp_id):
    """API: Get single drug product."""
    dp = drug_product_service.get_drug_product_by_id(dp_id)
    if not dp:
        return jsonify(success=False, message="Drug Product not found"), 404

    return jsonify({
        'id': dp.id,
        'code': dp.code,
        'pharm_form': dp.pharm_form,
        'technology': dp.technology,
        'classification': dp.classification,
        'storage_conditions': dp.storage_conditions,
        'transport_conditions': dp.transport_conditions,
        'holding_time': dp.holding_time,
        'development_approach': dp.development_approach,
        'development_site': dp.development_site,
        'launch_site': dp.launch_site,
        'release_site': dp.release_site,
        'routine_site': dp.routine_site,
        'demand_category': dp.demand_category,
        'demand_launch_year': dp.demand_launch_year,
        'demand_peak_year': dp.demand_peak_year,
        'peak_demand_range': dp.peak_demand_range,
        'commercial': dp.commercial,
        'strategic_technology': dp.strategic_technology,
        'd_and_dl_ops': dp.d_and_dl_ops,
        'last_refresh': dp.last_refresh.isoformat() if dp.last_refresh else None,
        'projects': [{'id': p.id, 'name': p.name} for p in dp.projects],
        'drug_substances': [{'id': ds.id, 'code': ds.code, 'inn': ds.inn} for ds in dp.drug_substances]
    })


@drug_product_api_bp.route('/', methods=['POST'])
@login_required
def api_create_drug_product():
    """API: Create new drug product."""
    data = request.json
    if not data or not data.get('code'):
        return jsonify(success=False, message="Code is required"), 400

    # Check for duplicate
    existing = drug_product_service.get_drug_product_by_code(data['code'])
    if existing:
        return jsonify(success=False, message=f"Code '{data['code']}' already exists"), 400

    dp = drug_product_service.create_drug_product(data)
    return jsonify(success=True, id=dp.id, message="Drug Product created"), 201


@drug_product_api_bp.route('/<int:dp_id>', methods=['PUT'])
@login_required
def api_update_drug_product(dp_id):
    """API: Update drug product (full or partial)."""
    data = request.json
    if not data:
        return jsonify(success=False, message="No data provided"), 400

    dp = DrugProduct.query.get(dp_id)
    if not dp:
        return jsonify(success=False, message="Drug Product not found"), 404

    for field, value in data.items():
        if hasattr(dp, field) and field not in ['id', 'created_at']:
            setattr(dp, field, value)

    from ..db import db
    db.session.commit()
    return jsonify(success=True, message="Drug Product updated")


@drug_product_api_bp.route('/<int:dp_id>/inline-update', methods=['PUT'])
@login_required
def api_inline_update_drug_product(dp_id):
    """API: Inline update single field."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data"), 400

    field, value = list(data.items())[0]
    dp, message = drug_product_service.inline_update_drug_product_field(dp_id, field, value)

    if not dp:
        return jsonify(success=False, message=message), 400
    return jsonify(success=True, message=message)


@drug_product_api_bp.route('/<int:dp_id>', methods=['DELETE'])
@login_required
def api_delete_drug_product(dp_id):
    """API: Delete drug product."""
    success, message = drug_product_service.delete_drug_product(dp_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)


# ============================================================================
# LINK MANAGEMENT ROUTES
# ============================================================================

@drug_product_api_bp.route('/<int:dp_id>/link-drug-substance/<int:ds_id>', methods=['POST'])
@login_required
def api_link_drug_substance(dp_id, ds_id):
    """API: Link a drug substance to this drug product."""
    success, message = drug_product_service.link_drug_substance(dp_id, ds_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)


@drug_product_api_bp.route('/<int:dp_id>/unlink-drug-substance/<int:ds_id>', methods=['DELETE'])
@login_required
def api_unlink_drug_substance(dp_id, ds_id):
    """API: Unlink a drug substance from this drug product."""
    success, message = drug_product_service.unlink_drug_substance(dp_id, ds_id)
    if not success:
        return jsonify(success=False, message=message), 404
    return jsonify(success=True, message=message)
