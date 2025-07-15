# backend/routes/product_routes.py
from flask import Blueprint, render_template, request, jsonify, g
from flask_login import login_required
from ..services import product_service

product_routes = Blueprint('products', __name__, url_prefix='/products')

@product_routes.route('/')
@login_required
def list_products():
    products = product_service.get_all_products(g.db_session)
    return render_template('products.html', title="Products", products=products)


@product_routes.route('/api/products/<int:product_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_product(product_id):
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400
    
    field, value = list(data.items())[0]
    
    product, message = product_service.inline_update_product_field(g.db_session, product_id, field, value)

    if not product:
        return jsonify(success=False, message=message), 400
        
    return jsonify(success=True, message=message, product={
        'product_id': product.product_id,
        'product_code': product.product_code,
        'product_name': product.product_name
        # Add other fields you might want to return
    })