# backend/routes/translation_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from ..db import db
from ..models import Challenge, ChallengeModalityDetail, Modality, ValueStep

translation_bp = Blueprint('translation', __name__, url_prefix='/translation')

# Define which tables have translatable fields
TRANSLATABLE_TABLES = {
    'value_steps': {
        'model': ValueStep,
        'display_name': 'Value Steps',
        'id_field': 'id',
        'fields': [
            ('name', 'name_en', 'Name'),
            ('description', 'description_en', 'Description'),
        ]
    },
    'challenges': {
        'model': Challenge,
        'display_name': 'Challenges',
        'id_field': 'id',
        'fields': [
            ('name', 'name_en', 'Name'),
            ('agnostic_description', 'agnostic_description_en', 'Agnostic Description'),
            ('agnostic_root_cause', 'agnostic_root_cause_en', 'Agnostic Root Cause'),
        ]
    },
    'challenge_modality_details': {
        'model': ChallengeModalityDetail,
        'display_name': 'Challenge Modality Details',
        'id_field': 'id',
        'fields': [
            ('specific_description', 'specific_description_en', 'Specific Description'),
            ('specific_root_cause', 'specific_root_cause_en', 'Specific Root Cause'),
            ('impact_details', 'impact_details_en', 'Impact Details'),
            ('maturity_details', 'maturity_details_en', 'Maturity Details'),
            ('trends_3_5_years', 'trends_3_5_years_en', 'Trends (3-5 Years)'),
        ]
    },
    'modalities': {
        'model': Modality,
        'display_name': 'Modalities',
        'id_field': 'modality_id',
        'fields': [
            ('modality_name', 'modality_name_en', 'Modality Name'),
            ('label', 'label_en', 'Label'),
            ('short_description', 'short_description_en', 'Short Description'),
            ('description', 'description_en', 'Description'),
        ]
    },
}


@translation_bp.route('/')
@login_required
def translation_page():
    """Render the translation management page."""
    tables = [
        {'key': key, 'name': config['display_name']}
        for key, config in TRANSLATABLE_TABLES.items()
    ]
    return render_template('translation.html', title="Translation", tables=tables)


@translation_bp.route('/api/table/<table_name>')
@login_required
def get_table_data(table_name):
    """Get all translatable data for a specific table."""
    if table_name not in TRANSLATABLE_TABLES:
        return jsonify(success=False, message=f"Unknown table: {table_name}"), 404

    config = TRANSLATABLE_TABLES[table_name]
    model = config['model']
    id_field = config['id_field']
    fields = config['fields']

    try:
        items = model.query.all()
        data = []

        for item in items:
            row = {
                'id': getattr(item, id_field),
                'fields': []
            }

            # Add identifier for display
            if table_name == 'challenge_modality_details':
                challenge_name = item.challenge.name if item.challenge else 'Unknown'
                modality_name = item.modality.modality_name if item.modality else 'Unknown'
                row['identifier'] = f"{challenge_name} / {modality_name}"
            elif hasattr(item, 'name'):
                row['identifier'] = item.name
            elif hasattr(item, 'modality_name'):
                row['identifier'] = item.modality_name
            else:
                row['identifier'] = f"ID: {row['id']}"

            for de_field, en_field, label in fields:
                row['fields'].append({
                    'label': label,
                    'de_field': de_field,
                    'en_field': en_field,
                    'de_value': getattr(item, de_field) or '',
                    'en_value': getattr(item, en_field) or '',
                })

            data.append(row)

        return jsonify(
            success=True,
            data=data,
            fields=[{'de_field': f[0], 'en_field': f[1], 'label': f[2]} for f in fields]
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=str(e)), 500


@translation_bp.route('/api/save', methods=['POST'])
@login_required
def save_translation():
    """Save a single field translation."""
    try:
        data = request.json
        table_name = data.get('table')
        item_id = data.get('id')
        field_name = data.get('field')
        value = data.get('value')

        if table_name not in TRANSLATABLE_TABLES:
            return jsonify(success=False, message=f"Unknown table: {table_name}"), 404

        config = TRANSLATABLE_TABLES[table_name]
        model = config['model']
        id_field = config['id_field']

        # Validate field is allowed
        allowed_fields = []
        for de_field, en_field, _ in config['fields']:
            allowed_fields.extend([de_field, en_field])

        if field_name not in allowed_fields:
            return jsonify(success=False, message=f"Field not allowed: {field_name}"), 400

        # Get and update item
        item = model.query.filter(getattr(model, id_field) == item_id).first()
        if not item:
            return jsonify(success=False, message=f"Item not found: {item_id}"), 404

        setattr(item, field_name, value if value else None)
        db.session.commit()

        return jsonify(success=True, message="Saved")

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=str(e)), 500
