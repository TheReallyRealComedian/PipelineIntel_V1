from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import product_service
from ..models import Product, ManufacturingChallenge, ProductSupplyChain

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