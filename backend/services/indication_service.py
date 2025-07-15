# backend/services/indication_service.py
from sqlalchemy.orm import Session, joinedload
from ..models import Indication

def get_all_indications(db_session: Session):
    return db_session.query(Indication).options(joinedload(Indication.product)).order_by(Indication.indication_name).all()