# backend/services/technology_service.py
from sqlalchemy.orm import Session
from ..models import ManufacturingTechnology

def get_all_technologies(db_session: Session):
    return db_session.query(ManufacturingTechnology).order_by(ManufacturingTechnology.technology_name).all()