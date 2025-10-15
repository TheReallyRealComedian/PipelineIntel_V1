# backend/routes/data_management_routes.py
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_required

from ..services.data_management_service import (
    analyze_json_import,
    finalize_import,
    analyze_json_import_with_resolution,
    analyze_process_template_import,
    finalize_process_template_import,
    import_full_database,
    _resolve_foreign_keys_for_technology,
    _resolve_foreign_keys_for_challenge,
    _resolve_foreign_keys_for_process_stage
)

from ..models import (
    Product, Indication, ManufacturingChallenge, ManufacturingTechnology,
    ProductSupplyChain, Modality, ManufacturingCapability, InternalFacility,
    ExternalPartner, ProcessStage, ProductTimeline, ProductRegulatoryFiling, 
    ProductManufacturingSupplier, ProcessTemplate, TemplateStage, ModalityChallenge
)

data_management_bp = Blueprint('data_management', __name__, url_prefix='/data-management')

ENTITY_MAP = {
    'products': {'model': Product, 'key': 'product_code'},
    'indications': {'model': Indication, 'key': 'indication_name'},
    'manufacturing_challenges': {
        'model': ManufacturingChallenge, 
        'key': 'challenge_name',
        'resolver': _resolve_foreign_keys_for_challenge
    },
    'manufacturing_technologies': {
        'model': ManufacturingTechnology, 
        'key': 'technology_name',
        'resolver': _resolve_foreign_keys_for_technology
    },
    'process_stages': {'model': ProcessStage, 'key': 'stage_name', 'resolver': _resolve_foreign_keys_for_process_stage},
    'process_templates': {'model': ProcessTemplate, 'key': 'template_name'},  # NEW: Added process templates
    'supply_chain': {'model': ProductSupplyChain, 'key': 'id'},
    'modalities': {'model': Modality, 'key': 'modality_name'},
    'manufacturing_capabilities': {'model': ManufacturingCapability, 'key': 'capability_name'},
    'internal_facilities': {'model': InternalFacility, 'key': 'facility_code'},
    'external_partners': {'model': ExternalPartner, 'key': 'company_name'},
    'product_timelines': {'model': ProductTimeline, 'key': 'timeline_id'},
    'product_regulatory_filings': {'model': ProductRegulatoryFiling, 'key': 'filing_id'},
    'product_manufacturing_suppliers': {'model': ProductManufacturingSupplier, 'key': 'supplier_id'},
    'modality_challenges': {'model': ModalityChallenge, 'key': 'modality_id'}
}


@data_management_bp.route('/')
@login_required
def data_management_page():
    return render_template('data_management.html', title="Data Management")


@data_management_bp.route('/full-import', methods=['POST'])
@login_required
def full_database_import():
    if 'full_backup_file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('data_management.data_management_page'))
    
    file = request.files['full_backup_file']
    
    if file.filename == '':
        flash('No file selected for full import.', 'warning')
        return redirect(url_for('data_management.data_management_page'))
    
    if file and file.filename.endswith('.json'):
        success, message = import_full_database(file.stream)
        flash(message, 'success' if success else 'danger')
    else:
        flash('Invalid file type. Please upload a .json backup file.', 'danger')
        
    return redirect(url_for('data_management.data_management_page'))


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

        # Special handling for process templates (they have nested structure)
        if entity_type == 'process_templates':
            analysis_result = analyze_process_template_import(json_data)
        else:
            # Use enhanced analysis for regular entities
            analysis_result = analyze_json_import_with_resolution(
                json_data,
                ENTITY_MAP[entity_type]['model'],
                ENTITY_MAP[entity_type]['key']
            )

        if analysis_result.get('success'):
            if analysis_result.get('needs_resolution'):
                # Store data for resolution step
                session['import_original_data'] = json_data
                session['import_entity_type'] = entity_type
                session['import_analysis_result'] = analysis_result
                return redirect(url_for('data_management.foreign_key_resolution'))
            else:
                # No resolution needed, proceed as normal
                session['import_preview_data'] = analysis_result['preview_data']
                session['import_entity_type'] = entity_type
                return redirect(url_for('data_management.import_preview'))
        else:
            flash(f"Analysis failed: {analysis_result.get('message')}", 'danger')
            return redirect(url_for('data_management.data_management_page'))

    except Exception as e:
        flash(f"Invalid JSON file: {e}", "danger")
        return redirect(url_for('data_management.data_management_page'))


@data_management_bp.route('/foreign-key-resolution')
@login_required
def foreign_key_resolution():
    analysis_result = session.get('import_analysis_result')
    entity_type = session.get('import_entity_type')
    original_data = session.get('import_original_data')

    if not analysis_result or not entity_type:
        flash("No resolution data found. Please start a new import.", "warning")
        return redirect(url_for('data_management.data_management_page'))

    # Prepare data for resolution template
    items_needing_resolution = [
        item for item in analysis_result['preview_data']
        if item['status'] == 'needs_resolution'
    ]

    missing_fields = list(analysis_result['missing_keys'].keys())

    return render_template(
        'foreign_key_resolution.html',
        title="Resolve Missing References",
        items_needing_resolution=items_needing_resolution,
        missing_fields=missing_fields,
        missing_keys=analysis_result['missing_keys'],
        suggestions=analysis_result['suggestions'],
        entity_type=entity_type,
        original_data=original_data
    )


@data_management_bp.route('/resolve-foreign-keys', methods=['POST'])
@login_required
def resolve_foreign_keys():
    """
    Apply foreign key resolutions, re-analyze the data,
    and store the result in the session for the preview page.
    """
    try:
        data = request.json
        resolutions = data.get('resolutions', {})
        entity_type = data.get('entity_type')
        original_data = data.get('original_data')

        # Update original data with resolved foreign keys
        resolved_data = []
        for index, item in enumerate(original_data):
            resolved_item = item.copy()
            if str(index) in resolutions:
                for field_name, resolution in resolutions[str(index)].items():
                    # Apply the resolution value to the item
                    if 'value' in resolution:
                        resolved_item[field_name] = resolution['value']
            resolved_data.append(resolved_item)

        # Re-run the import analysis on the now-resolved data
        if entity_type == 'process_templates':
            analysis_result = analyze_process_template_import(resolved_data)
        else:
            analysis_result = analyze_json_import(
                resolved_data,
                ENTITY_MAP[entity_type]['model'],
                ENTITY_MAP[entity_type]['key']
            )

        # Store the new preview data in the Flask session
        if analysis_result.get('success'):
            session['import_preview_data'] = analysis_result['preview_data']
            session['import_entity_type'] = entity_type
            session.modified = True
            return jsonify({'success': True, 'message': 'Resolutions applied and data re-analyzed.'})
        else:
            return jsonify({'success': False, 'message': 'Failed to re-analyze data after resolution.'}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


def create_missing_entity(field_name, entity_name, metadata):
    """
    Create missing entity based on field type.
    DEBUG VERSION with logging
    """
    print(f"DEBUG: create_missing_entity called with field_name={field_name}, entity_name={entity_name}, metadata={metadata}")

    from ..db import db
    from ..models import Modality

    if field_name == 'modality_name':
        print(f"DEBUG: Creating modality: {entity_name}")
        try:
            modality = Modality(
                modality_name=entity_name,
                modality_category=metadata.get('category', 'Other'),
                short_description=metadata.get('description', ''),
                description=metadata.get('description', '')
            )
            db.session.add(modality)
            db.session.flush()  # Get ID without committing
            print(f"DEBUG: Added modality to session: {modality.modality_id}")
            db.session.commit()
            print(f"DEBUG: Committed modality: {modality.modality_name}")
            return modality
        except Exception as e:
            print(f"DEBUG: Error creating modality: {e}")
            db.session.rollback()
            raise e

    # Add other entity types as needed
    raise ValueError(f"Unknown field type for creation: {field_name}")


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

    if not resolved_data or not entity_type or entity_type not in ENTITY_MAP:
        return jsonify(success=False, message="Invalid request data."), 400

    try:
        # Special handling for process templates
        if entity_type == 'process_templates':
            result = finalize_process_template_import(resolved_data)
        else:
            # Get the resolver if it exists
            entity_config = ENTITY_MAP[entity_type]
            resolver = entity_config.get('resolver')  # NEW: Get the resolver
            
            # Regular entity finalization - NOW PASS THE RESOLVER
            result = finalize_import(
                resolved_data, 
                entity_config['model'], 
                entity_config['key'],
                resolver  # NEW: Pass resolver as 4th argument
            )
        
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f"Import failed: {str(e)}"), 500