# backend/services/facility_service.py
from ..models import ManufacturingEntity

def get_all_entities():
    """Retrieves all manufacturing entities (internal and external), ordered by type and name."""
    return ManufacturingEntity.query.order_by(
        ManufacturingEntity.entity_type,
        ManufacturingEntity.entity_name
    ).all()