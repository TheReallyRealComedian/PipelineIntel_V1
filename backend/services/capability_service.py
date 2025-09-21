# backend/services/capability_service.py
from ..db import db
from ..models import ManufacturingCapability, Product


def get_all_capabilities():
    """Retrieves all manufacturing capabilities, ordered by category and name."""
    return ManufacturingCapability.query.order_by(
        ManufacturingCapability.capability_category,
        ManufacturingCapability.capability_name
    ).all()


def get_capability_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic capabilities table."""
    DEFAULT_COLUMNS = ['capability_name', 'capability_category', 'approach_category', 'complexity_weight', 'description']
    
    all_fields = ManufacturingCapability.get_all_fields()
    
    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    capabilities = get_all_capabilities()
    
    # Convert SQLAlchemy objects to dictionaries for the template
    capability_dicts = [{field: getattr(c, field) for field in all_fields} for c in capabilities]

    return {
        'items': capability_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'capability',
        'entity_plural': 'capabilities',
        'table_id': 'capabilitiesTable'
    }


def inline_update_capability_field(capability_id: int, field: str, value: any):
    """Updates a single field on a capability."""
    capability = ManufacturingCapability.query.get(capability_id)
    if not capability:
        return None, "Capability not found."

    if not hasattr(capability, field):
        return None, f"Field '{field}' does not exist."
    
    if field == 'capability_name':
        if not value or not str(value).strip():
            return None, "Capability Name cannot be empty."
        existing = ManufacturingCapability.query.filter(
            ManufacturingCapability.capability_name == value, 
            ManufacturingCapability.capability_id != capability_id
        ).first()
        if existing:
            return None, f"Capability Name '{value}' already exists."
    
    if field == 'complexity_weight':
        try:
            value = int(value)
            if value < 1 or value > 10:
                return None, "Complexity weight must be between 1 and 10."
        except (ValueError, TypeError):
            return None, "Complexity weight must be a number."

    setattr(capability, field, value)
    db.session.commit()
    return capability, "Capability updated."


def get_capability_gap_analysis(product_ids: list):
    """
    Analyzes the gap between required capabilities for a set of products and the capabilities
    available in the manufacturing network.

    This function will be fully implemented later. For now, it's a placeholder.
    It would query the 'all_product_requirements' view and compare against the 'entity_capabilities' table.
    """
    # Placeholder implementation
    print(f"Executing strategic query: Gap analysis for product IDs {product_ids}.")
    return {"gaps": [], "surpluses": []}


def get_facility_capability_matrix(facility_type: str = None):
    """
    Creates a matrix of internal facilities versus their capabilities.

    This function will be fully implemented later. For now, it's a placeholder.
    """
    # Placeholder implementation
    print(
        f"Executing strategic query: Facility capability matrix for type '{facility_type or 'all'}'."
    )
    return {}