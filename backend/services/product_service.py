# backend/services/product_service.py - CONVERTED VERSION
from sqlalchemy.orm import joinedload
from ..models import Product, Modality, all_product_requirements_view
from ..db import db  # Import db to use db.session

def get_all_products():
    """Get all products, eagerly loading the modality relationship to prevent N+1 queries."""
    return Product.query.options(joinedload(Product.modality)).order_by(Product.product_code).all()

def get_product_table_context(requested_columns_str: str = None):
    """Prepares the full context for the dynamic product table with correct relationship handling."""
    
    # FIX 2: Use the user-friendly 'modality_name' as the default column.
    DEFAULT_COLUMNS = ['modality_name', 'product_code', 'product_name', 'short_description', 'therapeutic_area', 'current_phase']
    
    # Get the base fields from our improved model method.
    all_fields = Product.get_all_fields()
    # Remove the non-user-friendly ID and add our "virtual" name field.
    if 'modality_id' in all_fields:
        all_fields.remove('modality_id')
    all_fields.insert(0, 'modality_name') # Add to the beginning for better default order

    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    products = get_all_products()
    
    # FIX 3: Manually construct the dictionaries to correctly handle the relationship.
    product_dicts = []
    for p in products:
        item_data = {}
        for field in all_fields:
            if field == 'modality_name':
                # For our virtual field, get the name from the related object.
                item_data[field] = p.modality.modality_name if p.modality else 'N/A'
            else:
                # For all other fields, get the attribute directly.
                item_data[field] = getattr(p, field, None)
        product_dicts.append(item_data)

    return {
        'products': product_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'product',
        'entity_plural': 'products',
        'table_id': 'productsTable'
    }


# BEFORE: def inline_update_product_field(db_session: Session, product_id: int, field: str, value: any):
# AFTER: Remove db_session parameter
def inline_update_product_field(product_id: int, field: str, value):
    """Updates a single field on a product for inline editing."""
    
    # Use Flask-SQLAlchemy query interface
    product = Product.query.get(product_id)
    if not product:
        return None, "Product not found."

    if not hasattr(product, field):
        return None, f"Field '{field}' does not exist."
    
    if field == 'product_code':
        if not value or not str(value).strip():
            return None, "Product Code cannot be empty."
        
        # Use Flask-SQLAlchemy query interface
        existing = Product.query.filter(
            Product.product_code == value, 
            Product.product_id != product_id
        ).first()
        if existing:
            return None, f"Product Code '{value}' already exists."

    setattr(product, field, value)
    db.session.commit()  # Use db.session directly
    return product, "Product updated."

# BEFORE: def get_product_with_requirements(db_session: Session, product_id: int):
# AFTER: Remove db_session parameter
def get_product_with_requirements(product_id: int):
    """Gets a single product and eagerly loads its combined requirements."""
    
    # Use Flask-SQLAlchemy query interface with joinedload
    product = Product.query.options(
        joinedload(Product.modality)
    ).get(product_id)
    
    if not product:
        return None, None

    # For views, we still need to use db.session.query
    requirements = db.session.query(all_product_requirements_view).filter_by(product_id=product_id).all()
    return product, requirements

# BEFORE: def get_products_by_modality(db_session: Session, modality_id: int):
# AFTER: Remove db_session parameter
def get_products_by_modality(modality_id: int):
    """Gets all products for a specific modality."""
    return Product.query.filter(Product.modality_id == modality_id).order_by(Product.product_name).all()