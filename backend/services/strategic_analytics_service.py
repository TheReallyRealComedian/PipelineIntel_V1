# backend/services/strategic_analytics_service.py
from sqlalchemy.orm import Session
from ..db import db
from ..models import Challenge, Modality, ChallengeModalityDetail, ValueStep
from datetime import datetime


def get_challenge_modality_matrix():
    """
    Returns matrix data for challenges vs modalities.

    Returns:
        {
            'challenges': [...],  # List of challenges with value_step
            'modalities': [...],  # List of modalities
            'matrix': {           # Dict mapping challenge_id -> modality_id -> detail
                challenge_id: {
                    modality_id: {
                        'applicable': True,
                        'impact_score': 1-5 or None,
                        'maturity_score': 1-5 or None,
                        'specific_description': str,
                        ...
                    }
                }
            },
            'value_steps': [...]  # Value steps in manufacturing order
        }
    """
    # Get all value steps in order (from DB)
    all_value_steps = ValueStep.get_ordered()
    value_step_order = {vs.id: vs.sort_order for vs in all_value_steps}

    # Get all challenges and sort by value chain order (from DB), then name
    challenges = Challenge.query.all()
    challenges.sort(key=lambda c: (
        value_step_order.get(c.value_step_id, 999),
        c.name or ''
    ))

    # Get all modalities
    modalities = Modality.query.order_by(Modality.modality_name).all()

    # Get all challenge-modality details
    details = ChallengeModalityDetail.query.all()

    # Build matrix lookup
    matrix = {}
    for detail in details:
        if detail.challenge_id not in matrix:
            matrix[detail.challenge_id] = {}
        matrix[detail.challenge_id][detail.modality_id] = {
            'applicable': True,
            'impact_score': detail.impact_score,
            'maturity_score': detail.maturity_score,
            'specific_description': detail.specific_description,
            'specific_root_cause': detail.specific_root_cause,
            'impact_details': detail.impact_details,
            'maturity_details': detail.maturity_details,
            'trends_3_5_years': detail.trends_3_5_years
        }

    # Return ALL value steps (for filter dropdown), in order
    value_steps = [
        {'id': vs.id, 'name': vs.name, 'sort_order': vs.sort_order}
        for vs in all_value_steps
    ]

    return {
        'challenges': [
            {
                'id': c.id,
                'name': c.name,
                'value_step': c.value_step,  # Uses @property for name
                'value_step_id': c.value_step_id,
                'agnostic_description': c.agnostic_description,
                'agnostic_root_cause': c.agnostic_root_cause
            } for c in challenges
        ],
        'modalities': [
            {
                'id': m.modality_id,
                'name': m.modality_name,
                'category': m.modality_category,
                'label': m.label
            } for m in modalities
        ],
        'matrix': matrix,
        'value_steps': value_steps
    }


def get_manufacturing_challenges_forecast(db_session: Session, years_ahead: int = 5):
    """
    Forecasts top manufacturing challenges based on the pipeline's modality mix
    and their challenge details over the next N years.

    TODO: Implement with new simplified schema (challenges + challenge_modality_details).
    """
    print(f"Executing strategic query: Manufacturing challenges forecast for the next {years_ahead} years.")
    return {}


def get_modality_complexity_ranking(db_session: Session, timeline_filter: int = None):
    """
    Ranks modalities by their manufacturing complexity.

    TODO: Implement with new simplified schema.
    """
    print(f"Executing strategic query: Modality complexity ranking for timeline '{timeline_filter or 'all time'}'.")
    return []


def get_weighted_challenges_data():
    """
    Returns challenge data weighted by impact and maturity scores.

    TODO: Implement with new simplified schema using challenge_modality_details table.
    For now, returns empty list until new query logic is implemented.
    """
    # Placeholder - will be implemented with new schema
    return []
