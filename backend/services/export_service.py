# backend/services/export_service.py
import json
import tiktoken
import datetime

from ..db import db


# Challenge-Felder, die modalitäts-agnostisch sind
AGNOSTIC_FIELDS = {
    'name': 'Challenge Name',
    'agnostic_description': 'General Description',
    'agnostic_root_cause': 'General Root Cause',
    'value_step': 'Value Step',
}

# Challenge-Felder, die modalitäts-spezifisch sind (aus ChallengeModalityDetail)
MODALITY_SPECIFIC_FIELDS = {
    'specific_description': 'Modality-Specific Description',
    'specific_root_cause': 'Modality-Specific Root Cause',
    'impact_score': 'Impact Score (1-5)',
    'impact_details': 'Impact Details',
    'maturity_score': 'Maturity Score (1-5)',
    'maturity_details': 'Maturity Details',
    'trends_3_5_years': 'Trends (3-5 Years)',
}


def get_export_page_context():
    """Gathers all necessary data for rendering the data export page."""
    from ..models import Modality

    modalities = Modality.query.order_by(Modality.modality_name).all()

    return {
        "modalities": modalities,
        "agnostic_fields": AGNOSTIC_FIELDS,
        "modality_specific_fields": MODALITY_SPECIFIC_FIELDS,
    }


def count_tokens(text: str) -> int:
    """Counts tokens in a string using tiktoken."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return len(text) // 4


def prepare_challenge_export(form_data: dict):
    """
    Prepares a JSON export of challenges based on selected modalities and fields.

    Returns challenges that have ChallengeModalityDetail entries for at least one
    of the selected modalities.
    """
    from ..models import Challenge, ChallengeModalityDetail, Modality

    # Get selected modality IDs
    selected_modality_ids = [
        int(id_str) for id_str in form_data.getlist('modality_ids')
        if id_str.isdigit()
    ]

    if not selected_modality_ids:
        return json.dumps({"error": "No modalities selected"}, indent=2), 0

    # Get selected fields
    selected_agnostic_fields = form_data.getlist('agnostic_fields')
    selected_specific_fields = form_data.getlist('specific_fields')

    if not selected_agnostic_fields and not selected_specific_fields:
        return json.dumps({"error": "No fields selected"}, indent=2), 0

    # Get modality names for output
    modalities = {m.modality_id: m.modality_name for m in Modality.query.all()}

    # Query challenges that have details for at least one selected modality
    challenges_with_details = db.session.query(Challenge).join(
        ChallengeModalityDetail
    ).filter(
        ChallengeModalityDetail.modality_id.in_(selected_modality_ids)
    ).distinct().order_by(Challenge.name).all()

    result = []

    for challenge in challenges_with_details:
        challenge_data = {}

        # Add agnostic fields
        for field in selected_agnostic_fields:
            if field == 'value_step':
                challenge_data['value_step'] = challenge.value_step
            elif hasattr(challenge, field):
                challenge_data[field] = getattr(challenge, field)

        # Add modality-specific details if any specific fields selected
        if selected_specific_fields:
            modality_details = {}

            for detail in challenge.modality_details:
                if detail.modality_id in selected_modality_ids:
                    modality_name = modalities.get(detail.modality_id, f"Modality {detail.modality_id}")
                    detail_data = {}

                    for field in selected_specific_fields:
                        if hasattr(detail, field):
                            detail_data[field] = getattr(detail, field)

                    if detail_data:
                        modality_details[modality_name] = detail_data

            if modality_details:
                challenge_data['modality_details'] = modality_details

        if challenge_data:
            result.append(challenge_data)

    json_string = json.dumps(result, default=str, indent=2, ensure_ascii=False)
    total_tokens = count_tokens(json_string)

    return json_string, total_tokens


def export_full_database():
    """Exports all data from all tables into a structured dictionary."""
    from .data_management_service import TABLE_IMPORT_ORDER

    all_data = {}

    def json_serializer(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return str(obj)

    # Add metadata for version tracking
    all_data['_meta'] = {
        'version': '2.0',
        'exported_at': datetime.datetime.now().isoformat(),
        'schema': 'projects_based',
        'tables': list(TABLE_IMPORT_ORDER),
    }

    for table_name in TABLE_IMPORT_ORDER:
        table = db.metadata.tables.get(table_name)
        if table is None or table_name == 'flask_sessions':
            continue

        result = db.session.execute(table.select())
        rows = [dict(row._mapping) for row in result]
        all_data[table_name] = rows

    return json.dumps(all_data, indent=2, default=json_serializer)
