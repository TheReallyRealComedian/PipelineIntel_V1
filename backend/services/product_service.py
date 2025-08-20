# backend/services/product_service.py
from sqlalchemy.orm import Session, joinedload
from ..models import Product, Modality, all_product_requirements_view

def get_all_products(db_session: Session):
    return db_session.query(Product).order_by(Product.product_code).all()

# New function to prepare all data for the template
def get_product_table_context(db_session: Session, requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic product table."""
    
    # Define default columns to show if none are requested
    # UPDATED: Replaced 'project_status' with 'short_description' for a better summary view.
    DEFAULT_COLUMNS = ['product_code', 'product_name', 'short_description', 'therapeutic_area', 'current_phase']
    
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

def get_product_with_requirements(db_session: Session, product_id: int):
    """
    Gets a single product and eagerly loads its combined requirements (both inherited from its modality
    and specific to the product) by querying the all_product_requirements view.
    """
    product = db_session.query(Product).options(
        joinedload(Product.modality)
    ).get(product_id)
    
    if not product:
        return None, None

    requirements = db_session.query(all_product_requirements_view).filter_by(product_id=product_id).all()
    return product, requirements

def get_products_by_modality(db_session: Session, modality_id: int):
    """Gets all products for a specific modality."""
    return db_session.query(Product).filter(Product.modality_id == modality_id).order_by(Product.product_name).all()