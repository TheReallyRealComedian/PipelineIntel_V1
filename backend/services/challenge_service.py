# backend/services/challenge_service.py
from sqlalchemy.orm import Session
from ..models import ManufacturingChallenge

def get_all_challenges(db_session: Session):
    return db_session.query(ManufacturingChallenge).order_by(ManufacturingChallenge.challenge_category, ManufacturingChallenge.challenge_name).all()