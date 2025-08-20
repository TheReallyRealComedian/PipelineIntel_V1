# backend/services/facility_service.py
from sqlalchemy.orm import Session
from ..models import ManufacturingEntity

def get_all_entities(db_session: Session):
    """Retrieves all manufacturing entities (internal and external), ordered by type and name."""
    return db_session.query(ManufacturingEntity).order_by(
        ManufacturingEntity.entity_type, 
        ManufacturingEntity.entity_name
    ).all()