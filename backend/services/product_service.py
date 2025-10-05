# backend/services/product_service.py
from sqlalchemy.orm import joinedload
from ..models import Product, Modality, ProcessTemplate, all_product_requirements_view
from ..db import db


def get_all_products():
    """Get all products, eagerly loading the modality relationship to prevent N+1 queries."""
    return Product.query.options(joinedload(Product.modality)).order_by(Product.product_code).all()


def get_product_table_context(requested_columns_str: str = None):
    """Prepares the full context for the dynamic product table with correct relationship handling."""

    DEFAULT_COLUMNS = [
        'modality_name', 'process_template_name', 'product_code',
        'product_name', 'short_description', 'therapeutic_area', 'current_phase'
    ]

    # Get the base fields from model
    all_fields = Product.get_all_fields()

    # Remove IDs and add user-friendly name fields
    if 'modality_id' in all_fields:
        all_fields.remove('modality_id')
    if 'process_template_id' in all_fields:
        all_fields.remove('process_template_id')

    # Add virtual fields
    all_fields.insert(0, 'modality_name')
    all_fields.insert(1, 'process_template_name')

    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    # Eager load both modality AND template
    products = Product.query.options(
        joinedload(Product.modality),
        joinedload(Product.process_template)
    ).order_by(Product.product_code).all()

    # Build product dictionaries with virtual fields
    product_dicts = []
    for p in products:
        item_data = {}
        for field in all_fields:
            if field == 'modality_name':
                item_data[field] = p.modality.modality_name if p.modality else 'N/A'
            elif field == 'process_template_name':
                item_data[field] = p.process_template.template_name if p.process_template else 'N/A'
            else:
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


def inline_update_product_field(product_id: int, field: str, value):
    """Updates a single field on a product for inline editing."""

    product = Product.query.get(product_id)
    if not product:
        return None, "Product not found."

    if not hasattr(product, field) and field not in ['modality_name', 'process_template_name']:
        return None, f"Field '{field}' does not exist."

    try:
        # Handle special virtual fields
        if field == 'modality_name':
            if value and value.strip():
                modality = Modality.query.filter_by(modality_name=value.strip()).first()
                if not modality:
                    return None, f"Modality '{value.strip()}' not found."
                product.modality_id = modality.modality_id

                # When modality changes, the old template may not be valid anymore
                if product.process_template_id:
                    old_template = ProcessTemplate.query.get(product.process_template_id)
                    if old_template and old_template.modality_id != modality.modality_id:
                        product.process_template_id = None  # Clear incompatible template
            else:
                product.modality_id = None
                product.process_template_id = None  # Clear template when modality cleared

        elif field == 'process_template_name':
            if value and value.strip():
                template = ProcessTemplate.query.filter_by(template_name=value.strip()).first()
                if not template:
                    return None, f"Process template '{value.strip()}' not found."

                # Validate template belongs to product's modality
                if product.modality_id and template.modality_id != product.modality_id:
                    modality = Modality.query.get(product.modality_id)
                    return None, (
                        f"Template '{template.template_name}' does not belong to "
                        f"modality '{modality.modality_name if modality else 'Unknown'}'"
                    )

                product.process_template_id = template.template_id
            else:
                product.process_template_id = None

        # Handle regular fields
        elif field == 'product_code':
            if not value or not str(value).strip():
                return None, "Product Code cannot be empty."
            product.product_code = str(value).strip()
        else:
            setattr(product, field, value)

        db.session.commit()
        return product, f"Updated {field} successfully."

    except ValueError as e:
        # Catch validation errors from the model's @validates decorator
        db.session.rollback()
        return None, str(e)
    except Exception as e:
        db.session.rollback()
        return None, f"Update failed: {str(e)}"


def get_product_with_requirements(product_id: int):
    """Gets a single product and eagerly loads its combined requirements."""

    product = Product.query.options(
        joinedload(Product.modality)
    ).get(product_id)

    if not product:
        return None, None

    requirements = db.session.query(all_product_requirements_view).filter_by(product_id=product_id).all()
    return product, requirements


def get_products_by_modality(modality_id: int):
    """Gets all products for a specific modality."""
    return Product.query.filter(Product.modality_id == modality_id).order_by(Product.product_name).all()