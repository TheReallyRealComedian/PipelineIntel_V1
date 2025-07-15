# backend/services/product_service.py
from sqlalchemy.orm import Session
from ..models import Product

def get_all_products(db_session: Session):
    return db_session.query(Product).order_by(Product.product_code).all()

def inline_update_product_field(db_session: Session, product_id: int, field: str, value: any):
    """Updates a single field on a product for inline editing."""
    product = db_session.query(Product).get(product_id)
    if not product:
        return None, "Product not found."

    # Basic validation
    if not hasattr(product, field):
        return None, f"Field '{field}' does not exist."
    
    # Add more specific validation here if needed, e.g., for unique fields
    if field == 'product_code':
        if not value or not str(value).strip():
            return None, "Product Code cannot be empty."
        existing = db_session.query(Product).filter(Product.product_code == value, Product.product_id != product_id).first()
        if existing:
            return None, f"Product Code '{value}' already exists."

    setattr(product, field, value)
    db_session.commit()
    return product, "Product updated."