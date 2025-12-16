from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import product_service
from ..db import db
from ..models import Product, ProductSupplyChain


# Blueprint for web pages
product_routes = Blueprint('products', __name__, url_prefix='/products')

# Blueprint for product-related APIs
product_api_bp = Blueprint('product_api', __name__, url_prefix='/api/products')


# --- Web Page Routes ---

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
    """Detailed product view."""
    from sqlalchemy.orm import joinedload

    product = Product.query.options(
        joinedload(Product.modality),
        joinedload(Product.indications),
        joinedload(Product.supply_chain).joinedload(ProductSupplyChain.manufacturing_entity),
    ).get_or_404(product_id)

    context = {
        'title': f"{product.product_name or product.product_code}",
        'product': product,
    }

    return render_template('product_detail.html', **context)


# --- API Routes ---

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


@product_api_bp.route('/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """
    Delete a product and all its related data.
    This will cascade delete:
    - All indications
    - All supply chain links
    - All process overrides
    - All requirements
    - All timeline milestones
    - All regulatory filings
    - All manufacturing suppliers
    """
    try:
        product = Product.query.get_or_404(product_id)

        product_code = product.product_code
        product_name = product.product_name or product_code

        db.session.delete(product)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Product "{product_name}" (Code: {product_code}) has been successfully deleted.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete product: {str(e)}'
        }), 500
