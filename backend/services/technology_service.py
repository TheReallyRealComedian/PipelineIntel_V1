# backend/services/technology_service.py
from ..db import db
from ..models import ManufacturingTechnology

def get_all_technologies():
    return ManufacturingTechnology.query.order_by(ManufacturingTechnology.technology_name).all()


def get_technology_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic technologies table."""
    
    DEFAULT_COLUMNS = ['technology_name', 'short_description', 'complexity_rating', 'innovation_potential']
    
    all_fields = ManufacturingTechnology.get_all_fields()
    
    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    technologies = get_all_technologies()
    
    # Convert SQLAlchemy objects to dictionaries for the template
    technology_dicts = [{field: getattr(t, field) for field in all_fields} for t in technologies]

    return {
        'items': technology_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'technology',
        'entity_plural': 'technologies',
        'table_id': 'technologiesTable'
    }


def inline_update_technology_field(technology_id: int, field: str, value: any):
    """Updates a single field on a manufacturing technology."""
    technology = ManufacturingTechnology.query.get(technology_id)
    if not technology:
        return None, "Technology not found."

    if not hasattr(technology, field):
        return None, f"Field '{field}' does not exist."
    
    # Add validation for unique fields
    if field == 'technology_name':
        if not value or not str(value).strip():
            return None, "Technology Name cannot be empty."
        existing = ManufacturingTechnology.query.filter(
            ManufacturingTechnology.technology_name == value, 
            ManufacturingTechnology.technology_id != technology_id
        ).first()
        if existing:
            return None, f"Technology Name '{value}' already exists."

    setattr(technology, field, value)
    db.session.commit()
    return technology, "Technology updated."