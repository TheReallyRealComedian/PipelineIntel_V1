# backend/services/challenge_service.py
from ..db import db
from ..models import Challenge, ChallengeModalityDetail, Modality, ValueStep


def get_all_challenges():
    """Get all challenges ordered by name."""
    return Challenge.query.order_by(Challenge.name).all()


def get_challenge_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic challenges table."""

    DEFAULT_COLUMNS = ['name', 'value_step', 'modalities_summary', 'agnostic_description']

    # Get base fields from model
    base_fields = Challenge.get_all_fields()

    # Add computed field for modalities
    all_fields = base_fields + ['modalities_summary']

    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    challenges = get_all_challenges()

    # Convert SQLAlchemy objects to dictionaries with modality info
    challenge_dicts = []
    for c in challenges:
        challenge_dict = {field: getattr(c, field, None) for field in base_fields}

        # Build modalities summary
        modality_summaries = []
        for detail in c.modality_details:
            if detail.modality:
                impact = f"I:{detail.impact_score}" if detail.impact_score else "I:–"
                maturity = f"M:{detail.maturity_score}" if detail.maturity_score else "M:–"
                modality_summaries.append(
                    f"{detail.modality.modality_name} ({impact}/{maturity})"
                )

        challenge_dict['modalities_summary'] = ', '.join(modality_summaries) if modality_summaries else '–'
        challenge_dicts.append(challenge_dict)

    return {
        'items': challenge_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'challenge',
        'entity_plural': 'challenges',
        'table_id': 'challengesTable'
    }


def inline_update_challenge_field(challenge_id: int, field: str, value):
    """Updates a single field on a challenge."""
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return None, "Challenge not found."

    # Handle value_step specially (convert name to ID)
    if field == 'value_step':
        if value:
            vs = ValueStep.query.filter_by(name=value).first()
            if not vs:
                return None, f"Value step '{value}' not found."
            challenge.value_step_id = vs.id
        else:
            challenge.value_step_id = None
        db.session.commit()
        return challenge, "Challenge updated."

    if not hasattr(challenge, field):
        return None, f"Field '{field}' does not exist."

    # Add validation for unique fields
    if field == 'name':
        if not value or not str(value).strip():
            return None, "Challenge Name cannot be empty."
        existing = Challenge.query.filter(
            Challenge.name == value,
            Challenge.id != challenge_id
        ).first()
        if existing:
            return None, f"Challenge Name '{value}' already exists."

    setattr(challenge, field, value)
    db.session.commit()
    return challenge, "Challenge updated."


def get_challenge_with_modality_details(challenge_id: int):
    """Get a challenge with all its modality-specific details."""
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return None

    return {
        'challenge': challenge,
        'modality_details': challenge.modality_details
    }


def get_challenges_by_modality(modality_id: int):
    """Get all challenges for a specific modality with their details."""
    details = ChallengeModalityDetail.query.filter_by(modality_id=modality_id).all()
    return details


def create_challenge(name: str, agnostic_description: str = None,
                     agnostic_root_cause: str = None, value_step: str = None,
                     value_step_id: int = None):
    """Create a new challenge.

    Args:
        value_step: Name of value step (will be looked up)
        value_step_id: Direct ID of value step (takes precedence)
    """
    # Check for duplicate name
    existing = Challenge.query.filter_by(name=name).first()
    if existing:
        return None, f"Challenge '{name}' already exists."

    # Resolve value_step_id
    resolved_value_step_id = value_step_id
    if not resolved_value_step_id and value_step:
        vs = ValueStep.query.filter_by(name=value_step).first()
        if vs:
            resolved_value_step_id = vs.id

    challenge = Challenge(
        name=name,
        agnostic_description=agnostic_description,
        agnostic_root_cause=agnostic_root_cause,
        value_step_id=resolved_value_step_id
    )
    db.session.add(challenge)
    db.session.commit()
    return challenge, "Challenge created."


def add_modality_detail(challenge_id: int, modality_id: int,
                        specific_description: str = None,
                        specific_root_cause: str = None,
                        impact_score: int = None,
                        impact_details: str = None,
                        maturity_score: int = None,
                        maturity_details: str = None,
                        trends_3_5_years: str = None):
    """Add or update modality-specific details for a challenge."""

    # Check if challenge and modality exist
    challenge = Challenge.query.get(challenge_id)
    modality = Modality.query.get(modality_id)

    if not challenge:
        return None, "Challenge not found."
    if not modality:
        return None, "Modality not found."

    # Check for existing detail
    detail = ChallengeModalityDetail.query.filter_by(
        challenge_id=challenge_id,
        modality_id=modality_id
    ).first()

    if detail:
        # Update existing
        if specific_description is not None:
            detail.specific_description = specific_description
        if specific_root_cause is not None:
            detail.specific_root_cause = specific_root_cause
        if impact_score is not None:
            detail.impact_score = impact_score
        if impact_details is not None:
            detail.impact_details = impact_details
        if maturity_score is not None:
            detail.maturity_score = maturity_score
        if maturity_details is not None:
            detail.maturity_details = maturity_details
        if trends_3_5_years is not None:
            detail.trends_3_5_years = trends_3_5_years
    else:
        # Create new
        detail = ChallengeModalityDetail(
            challenge_id=challenge_id,
            modality_id=modality_id,
            specific_description=specific_description,
            specific_root_cause=specific_root_cause,
            impact_score=impact_score,
            impact_details=impact_details,
            maturity_score=maturity_score,
            maturity_details=maturity_details,
            trends_3_5_years=trends_3_5_years
        )
        db.session.add(detail)

    db.session.commit()
    return detail, "Modality detail saved."


def delete_challenge(challenge_id: int):
    """Delete a challenge and all its modality details."""
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return False, "Challenge not found."

    db.session.delete(challenge)
    db.session.commit()
    return True, "Challenge deleted."
