# backend/services/capability_service.py
from ..models import ManufacturingCapability, Product


def get_all_capabilities():
    """Retrieves all manufacturing capabilities, ordered by category and name."""
    return ManufacturingCapability.query.order_by(
        ManufacturingCapability.capability_category,
        ManufacturingCapability.capability_name
    ).all()


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