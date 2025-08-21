# backend/services/indication_service.py
from sqlalchemy.orm import joinedload

from ..db import db
from ..models import Indication


def get_all_indications():
    return (
        Indication.query.options(joinedload(Indication.product))
        .order_by(Indication.indication_name)
        .all()
    )


def get_indication_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic indications table."""
    
    DEFAULT_COLUMNS = ['indication_name', 'therapeutic_area', 'development_phase', 'expected_launch_year']
    
    all_fields = Indication.get_all_fields()
    
    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    indications = get_all_indications()
    
    # Convert SQLAlchemy objects to dictionaries for the template
    indication_dicts = [{field: getattr(i, field) for field in all_fields} for i in indications]

    return {
        'items': indication_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'indication',
        'entity_plural': 'indications',
        'table_id': 'indicationsTable'
    }


def inline_update_indication_field(indication_id: int, field: str, value: any):
    """Updates a single field on an indication."""
    indication = Indication.query.get(indication_id)
    if not indication:
        return None, "Indication not found."

    if not hasattr(indication, field):
        return None, f"Field '{field}' does not exist."
    
    # Add validation for unique fields if needed
    if field == 'indication_name':
        if not value or not str(value).strip():
            return None, "Indication Name cannot be empty."
        # Note: indication_name is not unique across all indications, 
        # but you might want to check uniqueness within a product
        # existing = Indication.query.filter(
        #     Indication.indication_name == value, 
        #     Indication.indication_id != indication_id
        # ).first()
        # if existing:
        #     return None, f"Indication Name '{value}' already exists."

    setattr(indication, field, value)
    db.session.commit()
    return indication, "Indication updated."