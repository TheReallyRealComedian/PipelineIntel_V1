# backend/routes/data_management_routes.py
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_required

from ..services.data_management_service import analyze_json_import, finalize_import
from ..models import (
    Product, Indication, ManufacturingChallenge, ManufacturingTechnology,
    ProductSupplyChain, Modality, ManufacturingCapability, InternalFacility,
    ExternalPartner
)

data_management_bp = Blueprint('data_management', __name__, url_prefix='/data-management')

ENTITY_MAP = {
    'products': {'model': Product, 'key': 'product_code'},
    'indications': {'model': Indication, 'key': 'indication_name'},
    'manufacturing_challenges': {'model': ManufacturingChallenge, 'key': 'challenge_name'},
    'manufacturing_technologies': {'model': ManufacturingTechnology, 'key': 'technology_name'},
    'supply_chain': {'model': ProductSupplyChain, 'key': 'id'},
    'modalities': {'model': Modality, 'key': 'modality_name'},
    'manufacturing_capabilities': {'model': ManufacturingCapability, 'key': 'capability_name'},
    'internal_facilities': {'model': InternalFacility, 'key': 'facility_code'},
    'external_partners': {'model': ExternalPartner, 'key': 'company_name'},
}

@data_management_bp.route('/')
@login_required
def data_management_page():
    return render_template('data_management.html', title="Data Management")

@data_management_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_json_upload():
    if 'json_file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('data_management.data_management_page'))

    file = request.files['json_file']
    entity_type = request.form.get('entity_type')

    if file.filename == '' or not entity_type or entity_type not in ENTITY_MAP:
        flash('No file selected or invalid entity type.', 'warning')
        return redirect(url_for('data_management.data_management_page'))

    try:
        json_data = json.load(file.stream)
        if not isinstance(json_data, list):
            raise ValueError("JSON file must contain a list (array) of objects.")

        analysis_result = analyze_json_import(
            json_data,
            ENTITY_MAP[entity_type]['model'],
            ENTITY_MAP[entity_type]['key']
        )

        if analysis_result.get('success'):
            session['import_preview_data'] = analysis_result['preview_data']
            session['import_entity_type'] = entity_type
            return redirect(url_for('data_management.import_preview'))
        else:
            flash(f"Analysis failed: {analysis_result.get('message', 'Unknown error.')}", 'danger')
            return redirect(url_for('data_management.data_management_page'))

    except (json.JSONDecodeError, ValueError) as e:
        flash(f"Invalid JSON file: {e}", "danger")
        return redirect(url_for('data_management.data_management_page'))

@data_management_bp.route('/preview')
@login_required
def import_preview():
    preview_data = session.get('import_preview_data')
    entity_type = session.get('import_entity_type')

    if not preview_data or not entity_type:
        flash("No import preview data found. Please start a new import.", "warning")
        return redirect(url_for('data_management.data_management_page'))

    return render_template(
        'json_import_preview.html',
        title=f"Import Preview for {entity_type.replace('_', ' ').title()}",
        preview_data=preview_data,
        entity_type=entity_type
    )

@data_management_bp.route('/finalize', methods=['POST'])
@login_required
def finalize_json_import():
    resolved_data = request.json.get('resolved_data')
    entity_type = request.json.get('entity_type')

    if not resolved_data or not entity_type or not entity_type in ENTITY_MAP:
        return jsonify(success=False, message="Invalid request data."), 400

    result = finalize_import(
        resolved_data,
        ENTITY_MAP[entity_type]['model'],
        ENTITY_MAP[entity_type]['key']
    )

    session.pop('import_preview_data', None)
    session.pop('import_entity_type', None)

    return jsonify(result)