from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import product_service
from ..db import db
from ..models import Product, ManufacturingChallenge, ProductSupplyChain, ManufacturingTechnology, product_to_technology_association


# Blueprint for web pages (remains unchanged)
product_routes = Blueprint('products', __name__, url_prefix='/products')

# NEW: Blueprint specifically for product-related APIs
product_api_bp = Blueprint('product_api', __name__, url_prefix='/api/products')


# --- Web Page Routes (Unchanged) ---

@product_routes.route('/')
@login_required
def list_products():
    """List products."""
    requested_columns = request.args.get('columns')
    context = product_service.get_product_table_context(requested_columns)
    return render_template('products.html', title="Products", **context)


@product_routes.route('/<int:product_id>')
@login_required
def view_product_detail(product_id):
    """Detailed product view with comprehensive challenge management."""
    from sqlalchemy.orm import joinedload

    product = Product.query.options(
        joinedload(Product.modality),
        joinedload(Product.indications),
        joinedload(Product.technologies),
        joinedload(Product.supply_chain).joinedload(ProductSupplyChain.manufacturing_entity),
    ).get_or_404(product_id)

    context = {
        'title': f"{product.product_name or product.product_code}",
        'product': product,
    }

    return render_template('product_detail.html', **context)


# --- API Routes (Moved to the new blueprint with corrected paths) ---

@product_api_bp.route('/<int:product_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_product(product_id):
    """Update product inline."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    product, message = product_service.inline_update_product_field(product_id, field, value)

    if not product:
        return jsonify(success=False, message=message), 400

    return jsonify(success=True, message=message, product={
        'product_id': product.product_id,
        'product_code': product.product_code,
        'product_name': product.product_name
    })


@product_api_bp.route('/<int:product_id>/challenges', methods=['GET'])
@login_required
def get_product_challenges(product_id):
    """Get all challenge information for a product."""
    product = Product.query.get_or_404(product_id)

    try:
        inherited = product.get_inherited_challenges()
        explicit_relationships = product.get_explicit_challenge_relationships()
        effective = product.get_effective_challenges()

        return jsonify({
            'inherited': [
                {
                    'challenge_id': c.challenge_id,
                    'challenge_name': c.challenge_name,
                    'challenge_category': c.challenge_category,
                    'severity_level': c.severity_level,
                    'short_description': c.short_description
                } for c in inherited
            ],
            'explicit_relationships': explicit_relationships,
            'effective': [
                {
                    'challenge_id': item['challenge'].challenge_id,
                    'challenge_name': item['challenge'].challenge_name,
                    'challenge_category': item['challenge'].challenge_category,
                    'severity_level': item['challenge'].severity_level,
                    'source': item['source'],
                    'notes': item['notes']
                } for item in effective
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@product_api_bp.route('/<int:product_id>/challenges/<int:challenge_id>/exclude', methods=['POST'])
@login_required
def exclude_product_challenge(product_id, challenge_id):
    """Exclude an inherited challenge from a product."""
    product = Product.query.get_or_404(product_id)
    data = request.json or {}
    notes = data.get('notes', '')

    try:
        product.add_challenge_exclusion(challenge_id, notes)
        return jsonify({
            'success': True,
            'message': 'Challenge excluded successfully'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@product_api_bp.route('/<int:product_id>/challenges/<int:challenge_id>/include', methods=['POST'])
@login_required
def include_product_challenge(product_id, challenge_id):
    """Add a product-specific challenge."""
    product = Product.query.get_or_404(product_id)
    data = request.json or {}
    notes = data.get('notes', '')

    try:
        product.add_challenge_inclusion(challenge_id, notes)
        return jsonify({
            'success': True,
            'message': 'Challenge included successfully'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@product_api_bp.route('/<int:product_id>/challenges/<int:challenge_id>', methods=['DELETE'])
@login_required
def remove_product_challenge_relationship(product_id, challenge_id):
    """Remove any explicit challenge relationship."""
    product = Product.query.get_or_404(product_id)

    try:
        product.remove_challenge_relationship(challenge_id)
        return jsonify({
            'success': True,
            'message': 'Challenge relationship removed successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    


# Add these endpoints to backend/routes/product_routes.py in the product_api_bp blueprint

@product_api_bp.route('/<int:product_id>/technologies', methods=['GET'])
@login_required
def get_product_technologies(product_id):
    """
    Get all technologies for a product using the correct inheritance logic
    from the model.
    """
    from sqlalchemy.orm import joinedload
    from ..models import Product, ManufacturingTechnology

    product = Product.query.get_or_404(product_id)
    
    # Use the new, correct method from the model
    all_product_techs = product.get_inherited_technologies()
    
    # Group all unique technologies by stage for display
    technologies_by_stage = {}
    for tech in sorted(all_product_techs, key=lambda t: t.technology_name):
        # Eager load stage if not already loaded to prevent N+1 queries
        if 'stage' not in tech.__dict__:
             tech = ManufacturingTechnology.query.options(joinedload(ManufacturingTechnology.stage)).get(tech.technology_id)

        stage_name = tech.stage.stage_name if tech.stage else "Unassigned"
        if stage_name not in technologies_by_stage:
            technologies_by_stage[stage_name] = []
        technologies_by_stage[stage_name].append({
            'technology_id': tech.technology_id,
            'technology_name': tech.technology_name,
            'short_description': tech.short_description,
            'complexity_rating': tech.complexity_rating,
            'innovation_potential': tech.innovation_potential
        })
    
    return jsonify({
        'product_code': product.product_code,
        'product_name': product.product_name,
        'technologies_by_stage': technologies_by_stage
    })


@product_api_bp.route('/<int:product_id>/technologies/available', methods=['GET'])
@login_required
def get_available_technologies(product_id):
    """Get all available technologies grouped by stage, excluding already linked ones."""
    from sqlalchemy.orm import joinedload
    
    product = Product.query.get_or_404(product_id)
    
    # Get IDs of already linked technologies
    linked_tech_ids = db.session.query(product_to_technology_association.c.technology_id).filter(
        product_to_technology_association.c.product_id == product_id
    ).all()
    linked_tech_ids = [tid[0] for tid in linked_tech_ids]
    
    # Get all technologies NOT linked to this product
    available_techs = db.session.query(ManufacturingTechnology).filter(
        ~ManufacturingTechnology.technology_id.in_(linked_tech_ids) if linked_tech_ids else True
    ).options(joinedload(ManufacturingTechnology.stage)).order_by(
        ManufacturingTechnology.stage_id,
        ManufacturingTechnology.technology_name
    ).all()
    
    # Group by stage
    technologies_by_stage = {}
    for tech in available_techs:
        stage_name = tech.stage.stage_name if tech.stage else "Unassigned"
        if stage_name not in technologies_by_stage:
            technologies_by_stage[stage_name] = []
        technologies_by_stage[stage_name].append({
            'technology_id': tech.technology_id,
            'technology_name': tech.technology_name,
            'short_description': tech.short_description,
            'complexity_rating': tech.complexity_rating,
            'stage_name': stage_name
        })
    
    return jsonify({
        'available_technologies_by_stage': technologies_by_stage
    })


@product_api_bp.route('/<int:product_id>/technologies/<int:technology_id>', methods=['POST'])
@login_required
def add_product_technology(product_id, technology_id):
    """Link a technology to a product."""
    product = Product.query.get_or_404(product_id)
    technology = ManufacturingTechnology.query.get_or_404(technology_id)
    
    # Check if already linked
    if technology in product.technologies:
        return jsonify({
            'success': False,
            'message': 'Technology already linked to this product'
        }), 400
    
    # Add the link
    product.technologies.append(technology)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Technology "{technology.technology_name}" linked successfully'
    })


@product_api_bp.route('/<int:product_id>/technologies/<int:technology_id>', methods=['DELETE'])
@login_required
def remove_product_technology(product_id, technology_id):
    """Unlink a technology from a product."""
    product = Product.query.get_or_404(product_id)
    technology = ManufacturingTechnology.query.get_or_404(technology_id)
    
    # Check if linked
    if technology not in product.technologies:
        return jsonify({
            'success': False,
            'message': 'Technology not linked to this product'
        }), 400
    
    # Remove the link
    product.technologies.remove(technology)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Technology "{technology.technology_name}" unlinked successfully'
    })