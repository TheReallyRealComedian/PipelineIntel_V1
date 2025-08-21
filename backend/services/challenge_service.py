# backend/services/challenge_service.py
from ..db import db
from ..models import ManufacturingChallenge

def get_all_challenges():
    return ManufacturingChallenge.query.order_by(
        ManufacturingChallenge.challenge_category, 
        ManufacturingChallenge.challenge_name
    ).all()

def get_challenge_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic challenges table."""
    
    # UPDATED: Use 'short_description' instead of the longer 'explanation' field.
    DEFAULT_COLUMNS = ['challenge_name', 'challenge_category', 'short_description']
    
    all_fields = ManufacturingChallenge.get_all_fields()
    
    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    challenges = get_all_challenges()
    
    # Convert SQLAlchemy objects to dictionaries
    challenge_dicts = [{field: getattr(c, field) for field in all_fields} for c in challenges]

    return {
        'items': challenge_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'challenge',
        'entity_plural': 'challenges',  # ADD THIS LINE
        'table_id': 'challengesTable'
    }

def inline_update_challenge_field(challenge_id: int, field: str, value: any):
    """Updates a single field on a manufacturing challenge."""
    challenge = ManufacturingChallenge.query.get(challenge_id)
    if not challenge:
        return None, "Challenge not found."

    if not hasattr(challenge, field):
        return None, f"Field '{field}' does not exist."
    
    # Add validation for unique fields
    if field == 'challenge_name':
        if not value or not str(value).strip():
            return None, "Challenge Name cannot be empty."
        existing = ManufacturingChallenge.query.filter(
            ManufacturingChallenge.challenge_name == value, 
            ManufacturingChallenge.challenge_id != challenge_id
        ).first()
        if existing:
            return None, f"Challenge Name '{value}' already exists."

    setattr(challenge, field, value)
    db.session.commit()
    return challenge, "Challenge updated."