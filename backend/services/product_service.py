# backend/services/product_service.py
from sqlalchemy.orm import Session
from ..models import Product

def get_all_products(db_session: Session):
    return db_session.query(Product).order_by(Product.product_code).all()

# New function to prepare all data for the template
def get_product_table_context(db_session: Session, requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic product table."""
    
    # Define default columns to show if none are requested
    DEFAULT_COLUMNS = ['product_code', 'product_name', 'therapeutic_area', 'current_phase', 'project_status']
    
    all_fields = Product.get_all_fields()
    
    if requested_columns_str:
        # Filter requested columns to ensure they are valid fields
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    # Ensure selected_fields is not empty
    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    products = get_all_products(db_session)
    
    # Convert SQLAlchemy objects to dictionaries for easier template access
    product_dicts = [{field: getattr(p, field) for field in all_fields} for p in products]

    return {
        'products': product_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'product',
        'table_id': 'productsTable'
    }


def inline_update_product_field(db_session: Session, product_id: int, field: str, value: any):
    """Updates a single field on a product for inline editing."""
    # ... this function remains unchanged
    product = db_session.query(Product).get(product_id)
    if not product:
        return None, "Product not found."

    if not hasattr(product, field):
        return None, f"Field '{field}' does not exist."
    
    if field == 'product_code':
        if not value or not str(value).strip():
            return None, "Product Code cannot be empty."
        existing = db_session.query(Product).filter(Product.product_code == value, Product.product_id != product_id).first()
        if existing:
            return None, f"Product Code '{value}' already exists."

    setattr(product, field, value)
    db_session.commit()
    return product, "Product updated."