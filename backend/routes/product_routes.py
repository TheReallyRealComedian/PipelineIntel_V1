# backend/routes/product_routes.py
from flask import Blueprint, render_template, g
from flask_login import login_required
from ..services import product_service

product_routes = Blueprint('products', __name__, url_prefix='/products')

@product_routes.route('/')
@login_required
def list_products():
    products = product_service.get_all_products(g.db_session)
    return render_template('products.html', title="Products", products=products)