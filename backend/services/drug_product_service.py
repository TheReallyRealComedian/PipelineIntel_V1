# backend/services/drug_product_service.py
from sqlalchemy.orm import joinedload
from ..db import db
from ..models import DrugProduct


def get_all_drug_products():
    """Retrieves all drug products, ordered by code."""
    return DrugProduct.query.options(
        joinedload(DrugProduct.drug_substances)
    ).order_by(DrugProduct.code).all()


def get_drug_product_by_id(dp_id: int):
    """Retrieves a single drug product by ID with relationships."""
    return DrugProduct.query.options(
        joinedload(DrugProduct.projects),
        joinedload(DrugProduct.drug_substances)
    ).get(dp_id)


def get_drug_product_by_code(code: str):
    """Retrieves a single drug product by code."""
    return DrugProduct.query.filter_by(code=code).first()


def get_drug_product_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic drug products table."""
    DEFAULT_COLUMNS = ['code', 'pharm_form', 'technology', 'development_approach', 'demand_category', 'commercial']

    all_fields = DrugProduct.get_all_fields()

    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    drug_products = get_all_drug_products()

    # Convert SQLAlchemy objects to dictionaries for the template
    dp_dicts = []
    for dp in drug_products:
        dp_dict = {field: getattr(dp, field) for field in all_fields}
        # Add linked drug substance codes for display
        dp_dict['drug_substance_codes'] = ', '.join([ds.code for ds in dp.drug_substances]) if dp.drug_substances else None
        dp_dicts.append(dp_dict)

    return {
        'items': dp_dicts,
        'all_fields': all_fields + ['drug_substance_codes'],
        'selected_fields': selected_fields,
        'entity_type': 'drug_product',
        'entity_plural': 'drug_products',
        'table_id': 'drugProductsTable'
    }


def inline_update_drug_product_field(dp_id: int, field: str, value):
    """Updates a single field on a drug product."""
    dp = DrugProduct.query.get(dp_id)
    if not dp:
        return None, "Drug Product not found."

    if not hasattr(dp, field):
        return None, f"Field '{field}' does not exist."

    if field == 'code':
        if not value or not str(value).strip():
            return None, "Code cannot be empty."
        existing = DrugProduct.query.filter(
            DrugProduct.code == value,
            DrugProduct.id != dp_id
        ).first()
        if existing:
            return None, f"Code '{value}' already exists."

    setattr(dp, field, value)
    db.session.commit()
    return dp, "Drug Product updated."


def create_drug_product(data: dict):
    """Creates a new drug product."""
    dp = DrugProduct(**data)
    db.session.add(dp)
    db.session.commit()
    return dp


def delete_drug_product(dp_id: int):
    """Deletes a drug product by ID."""
    dp = DrugProduct.query.get(dp_id)
    if not dp:
        return False, "Drug Product not found."

    db.session.delete(dp)
    db.session.commit()
    return True, "Drug Product deleted."


def get_drug_products_by_pharm_form(pharm_form: str):
    """Get all drug products with a specific pharmaceutical form."""
    return DrugProduct.query.filter_by(pharm_form=pharm_form).order_by(DrugProduct.code).all()


def get_drug_products_by_classification(classification: str):
    """Get all drug products with a specific classification."""
    return DrugProduct.query.filter_by(classification=classification).order_by(DrugProduct.code).all()


def link_drug_substance(dp_id: int, ds_id: int):
    """Link a drug substance to a drug product."""
    from ..models import DrugSubstance
    dp = DrugProduct.query.get(dp_id)
    ds = DrugSubstance.query.get(ds_id)

    if not dp or not ds:
        return False, "Drug Product or Drug Substance not found."

    if ds not in dp.drug_substances:
        dp.drug_substances.append(ds)
        db.session.commit()
        return True, "Link created."
    return True, "Link already exists."


def unlink_drug_substance(dp_id: int, ds_id: int):
    """Unlink a drug substance from a drug product."""
    from ..models import DrugSubstance
    dp = DrugProduct.query.get(dp_id)
    ds = DrugSubstance.query.get(ds_id)

    if not dp or not ds:
        return False, "Drug Product or Drug Substance not found."

    if ds in dp.drug_substances:
        dp.drug_substances.remove(ds)
        db.session.commit()
        return True, "Link removed."
    return True, "No link existed."
