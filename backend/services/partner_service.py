# backend/services/partner_service.py
from sqlalchemy.orm import Session
from ..models import Partner

def get_all_partners(db_session: Session):
    return db_session.query(Partner).order_by(Partner.partner_name).all()