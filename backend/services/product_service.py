# backend/services/product_service.py
from sqlalchemy.orm import Session
from ..models import Product

def get_all_products(db_session: Session):
    return db_session.query(Product).order_by(Product.product_code).all()