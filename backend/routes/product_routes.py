# backend/routes/product_routes.py - CONVERTED VERSION
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services import product_service
# Remove g import - we don't need g.db_session anymore!

product_routes = Blueprint('products', __name__, url_prefix='/products')

@product_routes.route('/')
@login_required
def list_products():
    """List products - much cleaner now!"""
    requested_columns = request.args.get('columns')
    
    # BEFORE: context = product_service.get_product_table_context(g.db_session, requested_columns)
    # AFTER: Much simpler - no session passing needed
    context = product_service.get_product_table_context(requested_columns)
    
    return render_template('products.html', title="Products", **context)

@product_routes.route('/api/products/<int:product_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_product(product_id):
    """Update product inline - cleaner without session management."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400
    
    field, value = list(data.items())[0]
    
    # BEFORE: product, message = product_service.inline_update_product_field(g.db_session, product_id, field, value)
    # AFTER: Much simpler - no session passing
    product, message = product_service.inline_update_product_field(product_id, field, value)

    if not product:
        return jsonify(success=False, message=message), 400
        
    return jsonify(success=True, message=message, product={
        'product_id': product.product_id,
        'product_code': product.product_code,
        'product_name': product.product_name
    })

@product_routes.route('/<int:product_id>/details')
@login_required
def product_details(product_id):
    """Detailed product view with timeline, filings, and suppliers."""
    from ..models import Product, ProductTimeline, ProductRegulatoryFiling, ProductManufacturingSupplier
    
    product = Product.query.get_or_404(product_id)
    
    # Get related data
    timelines = ProductTimeline.query.filter_by(product_id=product_id).order_by(ProductTimeline.planned_date.desc()).all()
    filings = ProductRegulatoryFiling.query.filter_by(product_id=product_id).order_by(ProductRegulatoryFiling.submission_date.desc()).all()
    suppliers = ProductManufacturingSupplier.query.filter_by(product_id=product_id).order_by(ProductManufacturingSupplier.supply_type, ProductManufacturingSupplier.role).all()
    
    context = {
        'title': f"Product Details - {product.product_name}",
        'product': product,
        'timelines': timelines,
        'regulatory_filings': filings,
        'manufacturing_suppliers': suppliers,
    }
    
    return render_template('product_details.html', **context)