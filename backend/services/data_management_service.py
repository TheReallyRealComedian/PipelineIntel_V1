# backend/services/data_management_service.py
import json
import traceback
import difflib
from collections import defaultdict
from datetime import datetime, date
import re
from sqlalchemy import text


from ..db import db
from ..models import (
    Product, Indication, ManufacturingChallenge, ManufacturingTechnology,
    ProductSupplyChain, ManufacturingEntity, InternalFacility, ExternalPartner,
    Modality, ProcessStage, ProductTimeline, ProductRegulatoryFiling,
    ProductManufacturingSupplier, User, LLMSettings, ProcessTemplate, TemplateStage,
    ModalityRequirement, ProductRequirement, EntityCapability, ProductProcessOverride,
    ManufacturingCapability, ModalityChallenge
)

# This order is critical. Parents must be inserted before children.
TABLE_IMPORT_ORDER = [
    'users', 
    'modalities', 
    'process_stages',
    'manufacturing_capabilities', 
    'manufacturing_entities',
    'internal_facilities', 
    'external_partners', 
    'process_templates',
    'products', 
    'indications', 
    'manufacturing_technologies',
    'manufacturing_challenges', 
    'llm_settings',
    'modality_challenges',
    'template_stages', 'product_to_challenge', 'product_to_technology',
    'product_supply_chain', 'modality_requirements', 'product_requirements',
    'entity_capabilities', 'product_process_overrides', 'product_timelines',
    'product_regulatory_filings', 'product_manufacturing_suppliers'
]

# A comprehensive map from table name string to its ORM Model class
MODEL_MAP = {
    'users': User,
    'modalities': Modality,
    'process_stages': ProcessStage,
    'manufacturing_capabilities': ManufacturingCapability,
    'manufacturing_entities': ManufacturingEntity,
    'internal_facilities': InternalFacility,
    'external_partners': ExternalPartner,
    'process_templates': ProcessTemplate,
    'products': Product,
    'indications': Indication,
    'manufacturing_technologies': ManufacturingTechnology,
    'manufacturing_challenges': ManufacturingChallenge,
    'llm_settings': LLMSettings,
    'template_stages': TemplateStage,
    'product_supply_chain': ProductSupplyChain,
    'modality_requirements': ModalityRequirement,
    'product_requirements': ProductRequirement,
    'entity_capabilities': EntityCapability,
    'product_process_overrides': ProductProcessOverride,
    'product_timelines': ProductTimeline,
    'product_regulatory_filings': ProductRegulatoryFiling,
    'product_manufacturing_suppliers': ProductManufacturingSupplier,
    'modality_challenges': ModalityChallenge,
}


def import_full_database(file_stream):
    """
    Wipes the current database and imports data from a full backup JSON file.
    This is a destructive operation.
    """
    try:
        data = json.load(file_stream)

        # Verify that the JSON contains expected keys (table names)
        if not all(key in data for key in ['users', 'products', 'modalities']):
             return False, "Invalid backup file format. Essential tables are missing."

        # 1. Truncate tables in reverse order of dependencies
        db.session.execute(text('SET session_replication_role = replica;'))

        for table_name in reversed(TABLE_IMPORT_ORDER):
            if table_name in data:
                db.session.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;'))

        db.session.commit()

        # 2. Insert data in order of dependencies
        for table_name in TABLE_IMPORT_ORDER:
            if table_name in data and data[table_name]:
                table_data = data[table_name]
                model_class = MODEL_MAP.get(table_name)

                if model_class:
                    # Use bulk_insert_mappings for tables with an ORM model
                    db.session.bulk_insert_mappings(model_class, table_data)
                else:
                    # For simple association tables without a dedicated model class, use raw insert
                    table_obj = db.metadata.tables.get(table_name)
                    if table_obj is not None:
                        db.session.execute(table_obj.insert(), table_data)
                    else:
                        print(f"Warning: Could not find table or model for '{table_name}'. Skipping.")

        db.session.commit()

        # 3. Re-enable foreign key checks
        db.session.execute(text('SET session_replication_role = DEFAULT;'))
        db.session.commit()

        return True, "Database successfully imported."

    except Exception as e:
        db.session.rollback()
        # Ensure FK checks are re-enabled even on failure
        try:
            db.session.execute(text('SET session_replication_role = DEFAULT;'))
            db.session.commit()
        except:
            pass # Ignore if this fails (e.g., connection closed)

        traceback.print_exc()
        return False, f"An error occurred during import: {e}"


def analyze_json_import(json_data: list, model_class, unique_key_field: str):
    """
    Analyzes a list of JSON objects against existing data in the database.
    This function performs the comparison and generates a detailed preview.
    """
    preview_data = []
    try:
        product_map = {p.product_code: p for p in Product.query.all()} if model_class == ManufacturingChallenge else {}
        existing_items_query = model_class.query.all()
        existing_items_map = {getattr(item, unique_key_field): item for item in existing_items_query}

        for json_item in json_data:
            entry = {'status': 'error', 'action': 'skip', 'identifier': None, 'json_item': json_item, 'db_item': None, 'diff': {}, 'messages': []}
            identifier = json_item.get(unique_key_field)
            entry['identifier'] = identifier

            if not identifier:
                entry['messages'].append(f"Skipped: Item is missing the unique identifier field '{unique_key_field}'.")
                preview_data.append(entry)
                continue

            product_codes_from_json = set()
            if model_class == ManufacturingChallenge:
                product_codes_from_json = set(json_item.pop('product_codes', []))
                invalid_codes = [code for code in product_codes_from_json if code not in product_map]
                if invalid_codes:
                    entry['messages'].append(f"Warning: The following product codes were not found and will be ignored: {', '.join(invalid_codes)}")
                product_codes_from_json = {code for code in product_codes_from_json if code in product_map}

            existing_item = existing_items_map.get(identifier)

            if existing_item:
                entry['db_item'] = {c.name: getattr(existing_item, c.name) for c in existing_item.__table__.columns if not c.name.startswith('_')}

                # Determine changed fields
                if model_class == Product:
                    fields_to_check = [key for key in json_item.keys() if hasattr(existing_item, key)]
                    entry['diff'] = _enhanced_field_comparison(existing_item, json_item, fields_to_check)
                else:
                    # Original logic for other models
                    entry['diff'] = {}
                    for key, new_value in json_item.items():
                        if hasattr(existing_item, key):
                            old_value = getattr(existing_item, key)
                            if str(old_value or '') != str(new_value or ''):
                                entry['diff'][key] = {'old': old_value, 'new': new_value}

                if model_class == ManufacturingChallenge:
                    current_product_codes = {p.product_code for p in existing_item.products}
                    added = product_codes_from_json - current_product_codes
                    removed = current_product_codes - product_codes_from_json
                    if added or removed:
                        entry['diff']['product_links'] = {
                            'added': sorted(list(added)),
                            'removed': sorted(list(removed))
                        }

                is_dirty = bool(entry['diff'])

                if is_dirty:
                    entry['status'] = 'update'
                    entry['action'] = 'update'
                    entry['messages'].append(f"Item exists. Proposed changes: {len(entry['diff'])} field(s).")
                else:
                    entry['status'] = 'no_change'
                    entry['action'] = 'skip'
                    entry['messages'].append("Item already exists and matches the database.")
            else:
                entry['status'] = 'new'
                entry['action'] = 'add'
                entry['messages'].append("This is a new item that will be created.")
                if model_class == ManufacturingChallenge and product_codes_from_json:
                     entry['diff']['product_links'] = {'added': sorted(list(product_codes_from_json)), 'removed': []}

            preview_data.append(entry)

        return {"success": True, "preview_data": preview_data}
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "message": f"An unexpected analysis error occurred: {e}"}


def analyze_json_import_with_resolution(json_data: list, model_class, unique_key_field: str):
    """
    Enhanced analysis that detects missing foreign keys and suggests matches.
    """
    preview_data = []
    missing_keys = defaultdict(set)  # {field_name: {missing_values}}
    suggestions = {}  # {field_name: {missing_value: [suggestions]}}

    try:
        # Get foreign key field mappings for this model
        foreign_key_fields = get_foreign_key_fields(model_class)

        # Pre-fetch existing entities for suggestions
        existing_entities = {}
        for field_name, (related_model, lookup_field) in foreign_key_fields.items():
            entities = related_model.query.all()
            existing_entities[field_name] = {
                getattr(entity, lookup_field): entity
                for entity in entities
            }

        # Analyze each JSON item
        for json_item in json_data:
            entry = {
                'status': 'pending_resolution',
                'action': 'add',
                'identifier': json_item.get(unique_key_field),
                'json_item': json_item,
                'missing_foreign_keys': {},
                'messages': []
            }

            # Check for missing foreign keys
            has_missing_keys = False
            for field_name, (related_model, lookup_field) in foreign_key_fields.items():
                if field_name in json_item:
                    lookup_value = json_item[field_name]
                    if lookup_value not in existing_entities[field_name]:
                        # Missing foreign key found
                        missing_keys[field_name].add(lookup_value)
                        has_missing_keys = True

                        # Generate suggestions
                        if lookup_value not in suggestions.get(field_name, {}):
                            if field_name not in suggestions:
                                suggestions[field_name] = {}
                            suggestions[field_name][lookup_value] = generate_suggestions(
                                lookup_value,
                                list(existing_entities[field_name].keys())
                            )

                        entry['missing_foreign_keys'][field_name] = lookup_value

            if has_missing_keys:
                entry['status'] = 'needs_resolution'
                entry['messages'].append("Missing foreign key references found")
            else:
                entry['status'] = 'ready'
                entry['messages'].append("All foreign key references validated")

            preview_data.append(entry)

        return {
            "success": True,
            "preview_data": preview_data,
            "missing_keys": dict(missing_keys),
            "suggestions": suggestions,
            "needs_resolution": any(missing_keys.values())
        }

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "message": f"Analysis error: {e}"}


def get_foreign_key_fields(model_class):
    """
    Returns mapping of foreign key fields for a model.
    Format: {field_name: (related_model_class, lookup_field)}
    """
    from ..models import Product, Modality, ProcessStage, ManufacturingCapability

    mappings = {
        Product: {
            'modality_name': (Modality, 'modality_name'),
        },
        # Add other model mappings as needed
    }

    return mappings.get(model_class, {})


def generate_suggestions(missing_value, existing_values, max_suggestions=3):
    """
    Generate smart suggestions for missing foreign key values.
    """
    suggestions = []

    # Use difflib for fuzzy matching
    matches = difflib.get_close_matches(
        missing_value,
        existing_values,
        n=max_suggestions,
        cutoff=0.6
    )

    for match in matches:
        similarity = difflib.SequenceMatcher(None, missing_value.lower(), match.lower()).ratio()
        suggestions.append({
            'value': match,
            'similarity': similarity,
            'reason': f"{similarity:.0%} match"
        })

    return suggestions


def _resolve_foreign_keys_for_technology(item, existing_technologies):
    """
    Resolves foreign keys for manufacturing technologies.
    Converts name-based references to ID-based references.
    """
    from ..models import ProcessStage, Modality, ProcessTemplate
    
    resolved_item = item.copy()
    
    # Resolve stage_name → stage_id (REQUIRED)
    if 'stage_name' in resolved_item:
        stage = ProcessStage.query.filter_by(stage_name=resolved_item['stage_name']).first()
        if stage:
            resolved_item['stage_id'] = stage.stage_id
            del resolved_item['stage_name']
        else:
            raise ValueError(f"Stage '{resolved_item['stage_name']}' not found")
    
    # Resolve modality_name → modality_id (OPTIONAL)
    if 'modality_name' in resolved_item:
        modality = Modality.query.filter_by(modality_name=resolved_item['modality_name']).first()
        if modality:
            resolved_item['modality_id'] = modality.modality_id
            del resolved_item['modality_name']
        else:
            raise ValueError(f"Modality '{resolved_item['modality_name']}' not found. Make sure to import modalities first.")
    
    # Resolve template_name → template_id (OPTIONAL)
    if 'template_name' in resolved_item:
        template = ProcessTemplate.query.filter_by(template_name=resolved_item['template_name']).first()
        if template:
            resolved_item['template_id'] = template.template_id
            # Auto-set modality_id if not already set (template knows its modality)
            if 'modality_id' not in resolved_item:
                resolved_item['modality_id'] = template.modality_id
            del resolved_item['template_name']
        else:
            raise ValueError(f"Template '{resolved_item['template_name']}' not found. Make sure to import process templates first.")
    
    return resolved_item

def _parse_date(date_string):
    """Helper function to parse date strings into date objects."""
    if not date_string:
        return None

    if isinstance(date_string, date):
        return date_string

    if isinstance(date_string, str):
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d.%m.%Y', '%Y-%m']:
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue

    return None


def _enhanced_field_comparison(existing_obj, json_data, fields_to_check):
    """
    Enhanced field comparison that handles the new Product fields properly.
    """
    changed_fields = {}

    for field in fields_to_check:
        json_value = json_data.get(field)
        existing_value = getattr(existing_obj, field, None)

        # Special handling for date fields
        if field in ['submission_date', 'approval_date', 'ppq_completion_date']:
            json_value = _parse_date(json_value)

        # Special handling for JSONB fields - normalize for comparison
        if field in ['regulatory_details', 'ppq_details', 'ds_suppliers', 'dp_suppliers',
                    'device_partners', 'operational_risks', 'timeline_risks',
                    'supply_chain_risks', 'clinical_trials']:
            if json_value is None and existing_value is None:
                continue
            elif json_value != existing_value:
                changed_fields[field] = {'old': existing_value, 'new': json_value}

        # Standard field comparison
        elif json_value != existing_value:
            # Handle None comparisons properly
            if json_value is None and existing_value == '':
                continue
            if existing_value is None and json_value == '':
                continue
            changed_fields[field] = {'old': existing_value, 'new': json_value}

    return changed_fields


def _process_product_related_tables(product_obj, json_data):
    """
    Process and create related table entries for Products during import.
    Handles ProductTimeline, ProductRegulatoryFiling, and ProductManufacturingSupplier.

    Args:
        product_obj: SQLAlchemy Product object (must have product_id)
        json_data: Dictionary containing the JSON import data
    """
    try:
        # Ensure we have a valid product object with an ID
        if not hasattr(product_obj, 'product_id') or product_obj.product_id is None:
            print(f"Warning: Product object has no product_id, skipping related tables")
            return

        # ==================== TIMELINE MILESTONES ====================
        if 'timeline_milestones' in json_data and isinstance(json_data['timeline_milestones'], list):
            for milestone_data in json_data['timeline_milestones']:
                if isinstance(milestone_data, dict):
                    timeline = ProductTimeline(
                        product_id=product_obj.product_id,
                        milestone_type=milestone_data.get('milestone_type'),
                        milestone_name=milestone_data.get('milestone_name'),
                        planned_date=_parse_date(milestone_data.get('planned_date')),
                        actual_date=_parse_date(milestone_data.get('actual_date')),
                        variance_days=milestone_data.get('variance_days'),
                        baseline_plan=milestone_data.get('baseline_plan'),
                        status=milestone_data.get('status'),
                        notes=milestone_data.get('notes')
                    )
                    db.session.add(timeline)

        # ==================== REGULATORY FILINGS ====================
        if 'regulatory_filings' in json_data and isinstance(json_data['regulatory_filings'], list):
            for filing_data in json_data['regulatory_filings']:
                if isinstance(filing_data, dict):
                    filing = ProductRegulatoryFiling(
                        product_id=product_obj.product_id,
                        indication=filing_data.get('indication'),
                        geography=filing_data.get('geography'),
                        filing_type=filing_data.get('filing_type'),
                        submission_date=_parse_date(filing_data.get('submission_date')),
                        approval_date=_parse_date(filing_data.get('approval_date')),
                        status=filing_data.get('status'),
                        designations=filing_data.get('designations'),
                        regulatory_authority=filing_data.get('regulatory_authority'),
                        notes=filing_data.get('notes')
                    )
                    db.session.add(filing)

        # ==================== MANUFACTURING SUPPLIERS ====================
        if 'manufacturing_suppliers' in json_data and isinstance(json_data['manufacturing_suppliers'], list):
            for supplier_data in json_data['manufacturing_suppliers']:
                if isinstance(supplier_data, dict):
                    supplier = ProductManufacturingSupplier(
                        product_id=product_obj.product_id,
                        supply_type=supplier_data.get('supply_type'),
                        supplier_name=supplier_data.get('supplier_name'),
                        site_name=supplier_data.get('site_name'),
                        site_location=supplier_data.get('site_location'),
                        role=supplier_data.get('role'),
                        status=supplier_data.get('status'),
                        technology=supplier_data.get('technology'),
                        start_date=_parse_date(supplier_data.get('start_date')),
                        qualification_date=_parse_date(supplier_data.get('qualification_date')),
                        notes=supplier_data.get('notes')
                    )
                    db.session.add(supplier)

        # Auto-populate suppliers from JSONB fields if structured data not provided
        _auto_populate_suppliers_from_jsonb(product_obj)

    except Exception as e:
        print(f"Warning: Error processing product related tables for {getattr(product_obj, 'product_code', 'unknown')}: {e}")
        import traceback
        traceback.print_exc()


def _auto_populate_suppliers_from_jsonb(product):
    """
    Auto-populate ProductManufacturingSupplier records from ds_suppliers/dp_suppliers JSONB fields.
    This provides backward compatibility and convenience.
    """
    try:
        # Only create supplier records if they don't already exist
        existing_suppliers = ProductManufacturingSupplier.query.filter_by(product_id=product.product_id).count()
        if existing_suppliers > 0:
            return  # Skip if suppliers already exist

        # Process DS suppliers
        if product.ds_suppliers and isinstance(product.ds_suppliers, list):
            for ds_data in product.ds_suppliers:
                if isinstance(ds_data, dict) and ds_data.get('name'):
                    supplier = ProductManufacturingSupplier(
                        product_id=product.product_id,
                        supply_type='DS',
                        supplier_name=ds_data.get('name'),
                        site_name=ds_data.get('site'),
                        role=ds_data.get('role', 'Primary'),
                        status=ds_data.get('status', 'Active')
                    )
                    db.session.add(supplier)

        # Process DP suppliers
        if product.dp_suppliers and isinstance(product.dp_suppliers, list):
            for dp_data in product.dp_suppliers:
                if isinstance(dp_data, dict) and dp_data.get('name'):
                    supplier = ProductManufacturingSupplier(
                        product_id=product.product_id,
                        supply_type='DP',
                        supplier_name=dp_data.get('name'),
                        site_name=dp_data.get('site'),
                        role=dp_data.get('role', 'Primary'),
                        status=dp_data.get('status', 'Active')
                    )
                    db.session.add(supplier)

        # Process device partners
        if product.device_partners and isinstance(product.device_partners, list):
            for device_data in product.device_partners:
                if isinstance(device_data, dict) and device_data.get('partner'):
                    supplier = ProductManufacturingSupplier(
                        product_id=product.product_id,
                        supply_type='Device',
                        supplier_name=device_data.get('partner'),
                        role='Device Partner',
                        status=device_data.get('status', 'Active'),
                        technology=device_data.get('type')
                    )
                    db.session.add(supplier)

    except Exception as e:
        print(f"Warning: Error auto-populating suppliers for {getattr(product, 'product_code', 'unknown')}: {e}")
        import traceback
        traceback.print_exc()


def _separate_product_data(json_data):
    """
    Separate main Product fields from related table data.
    Returns (main_product_data, related_table_data)
    """
    # Fields that go to related tables, not the main Product record
    related_table_fields = [
        'timeline_milestones',
        'regulatory_filings',
        'manufacturing_suppliers'
    ]

    main_product_data = {}
    related_table_data = {}

    for key, value in json_data.items():
        if key in related_table_fields:
            related_table_data[key] = value
        else:
            main_product_data[key] = value

    return main_product_data, related_table_data



def finalize_import(resolved_data, model_class, unique_key_field):
    """
    Finalizes the import by creating or updating database entries.
    Now calls the custom resolver if one is defined in ENTITY_MAP.
    """
    from ..db import db
    success_count = 0
    error_count = 0
    errors = []

    try:
        # Get the resolver function if it exists (from ENTITY_MAP in routes)
        # We need to import ENTITY_MAP here or pass resolver as parameter
        from ..routes.data_management_routes import ENTITY_MAP

        # Find which entity this model_class belongs to
        resolver_func = None
        for entity_type, config in ENTITY_MAP.items():
            if config['model'] == model_class:
                resolver_func = config.get('resolver')
                break

        for entry in resolved_data:
            identifier = None
            try:
                data = entry['json_item'].copy()
                identifier = data.get(unique_key_field)

                # CRITICAL: Call resolver if it exists
                if resolver_func:
                    # Get existing instances for the resolver
                    existing_instances = model_class.query.all()
                    data = resolver_func(data, existing_instances)

                # The resolver should return None if the item should be skipped
                if data is None:
                    continue

                # Check if record already exists
                existing_record = model_class.query.filter(
                    getattr(model_class, unique_key_field) == identifier
                ).first()

                if existing_record:
                    # Update existing record
                    for key, value in data.items():
                        if hasattr(existing_record, key):
                            setattr(existing_record, key, value)
                    success_count += 1
                else:
                    # Create new record
                    new_obj = model_class(**data)
                    db.session.add(new_obj)
                    success_count += 1

            except Exception as e:
                error_count += 1
                error_id = f"'{identifier}'" if identifier else "an unknown record"
                errors.append(f"Failed to process {error_id}: {str(e)}")
                db.session.rollback()
                continue

        # Commit all changes
        db.session.commit()

        return {
            "success": True,
            "message": f"Import completed: {success_count} records processed, {error_count} errors",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }

    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": f"Import failed: {str(e)}",
            "errors": [str(e)]
        }

def analyze_process_template_import(json_data):
    """
    Analyze process template import data with nested stages.
    Returns analysis with preview data for user review.
    """
    from ..models import ProcessTemplate, ProcessStage, Modality
    from ..db import db

    try:
        preview_data = []
        missing_keys = {}
        suggestions = {}
        needs_resolution = False

        for index, item in enumerate(json_data):
            preview_item = {
                'index': index,
                'json_item': item,
                'identifier': item.get('template_name', f'Item {index}'),
                'action': 'skip',  # Default to skip
                'status': 'error',  # Will be updated based on analysis
                'messages': [],     # Changed from 'issues' to match template expectation
                'diff': {},         # Added to match template expectation
                'db_item': None,    # Added to match template expectation
                'stage_count': 0
            }


            # Check required fields
            if not item.get('template_name'):
                preview_item['messages'].append('Missing template_name')
                preview_item['status'] = 'error'
                preview_data.append(preview_item)
                continue

            # Check if template already exists
            existing_template = ProcessTemplate.query.filter_by(
                template_name=item['template_name']
            ).first()

            if existing_template:
                            preview_item['action'] = 'update'
                            preview_item['status'] = 'update'
                            
                            # FIX: Convert the SQLAlchemy object to a simple dictionary
                            preview_item['db_item'] = {
                                'template_name': existing_template.template_name,
                                'description': existing_template.description,
                                'modality_name': existing_template.modality.modality_name if existing_template.modality else None
                            }
                            
                            preview_item['messages'].append(f'Template exists - will update existing template')
                            # Add diff information for updates
                            preview_item['diff']['description'] = {
                                'old': existing_template.description or '',
                                'new': item.get('description', '')
                            }
                            if item.get('modality_name') != (existing_template.modality.modality_name if existing_template.modality else None):
                                preview_item['diff']['modality'] = {
                                    'old': existing_template.modality.modality_name if existing_template.modality else 'None',
                                    'new': item.get('modality_name', 'None')
                                }
            else:
                preview_item['action'] = 'add'
                preview_item['status'] = 'new'
                preview_item['messages'].append('New template - will be created')

            # Check modality reference
            modality_name = item.get('modality_name')
            if modality_name:
                modality = Modality.query.filter_by(modality_name=modality_name).first()
                if not modality:
                    preview_item['messages'].append(f'Modality "{modality_name}" not found')
                    preview_item['status'] = 'needs_resolution'
                    needs_resolution = True

                    # Add to missing keys for resolution UI
                    if 'modality_name' not in missing_keys:
                        missing_keys['modality_name'] = set()
                    missing_keys['modality_name'].add(modality_name)

                    # Suggest similar modalities
                    if 'modality_name' not in suggestions:
                        suggestions['modality_name'] = {}
                    all_modalities = [m.modality_name for m in Modality.query.all()]
                    suggestions['modality_name'][modality_name] = all_modalities[:5]  # Top 5 suggestions

            # Analyze stages
            stages = item.get('stages', [])
            preview_item['stage_count'] = len(stages)
            stage_issues = []

            for stage_index, stage_item in enumerate(stages):
                stage_name = stage_item.get('stage_name')
                if not stage_name:
                    stage_issues.append(f'Stage {stage_index + 1}: Missing stage_name')
                    continue

                # Check if stage exists
                existing_stage = ProcessStage.query.filter_by(stage_name=stage_name).first()
                if not existing_stage:
                    stage_issues.append(f'Stage "{stage_name}" not found in system')
                    preview_item['status'] = 'needs_resolution'
                    needs_resolution = True

                    # Add to missing keys
                    if 'stage_name' not in missing_keys:
                        missing_keys['stage_name'] = set()
                    missing_keys['stage_name'].add(stage_name)

                    # Suggest similar stages
                    if 'stage_name' not in suggestions:
                        suggestions['stage_name'] = {}
                    all_stages = [s.stage_name for s in ProcessStage.query.all()]
                    suggestions['stage_name'][stage_name] = all_stages[:5]

            if stage_issues:
                preview_item['messages'].extend(stage_issues)

            # Add stage count to messages
            preview_item['messages'].append(f'Contains {len(stages)} stages')

            # If no issues and not needs_resolution, confirm status
            if not stage_issues and preview_item['status'] not in ['needs_resolution', 'error']:
                if preview_item['status'] != 'update':
                    preview_item['status'] = 'new'

            preview_data.append(preview_item)

        # Convert sets to lists for JSON serialization
        for key in missing_keys:
            missing_keys[key] = list(missing_keys[key])

        return {
            'success': True,
            'preview_data': preview_data,
            'needs_resolution': needs_resolution,
            'missing_keys': missing_keys,
            'suggestions': suggestions,
            'total_templates': len(json_data),
            'total_stages': sum(len(item.get('stages', [])) for item in json_data)
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Analysis failed: {str(e)}'
        }


def finalize_process_template_import(resolved_data):
    """
    Finalize the import of process templates with their associated template stages.
    """
    from ..models import ProcessTemplate, TemplateStage, ProcessStage, Modality
    from ..db import db

    added_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    error_messages = []

    try:
        for item in resolved_data:
            action = item.get('action')
            data = item.get('data')

            if action == 'skip':
                skipped_count += 1
                continue

            try:
                template_name = data.get('template_name')
                if not template_name:
                    failed_count += 1
                    error_messages.append(f"Template missing name: {data}")
                    continue

                # Find or create the template
                if action == 'update':
                    template = ProcessTemplate.query.filter_by(template_name=template_name).first()
                    if not template:
                        failed_count += 1
                        error_messages.append(f"Template not found for update: {template_name}")
                        continue
                else:  # action == 'add'
                    template = ProcessTemplate()

                # Set template properties
                template.template_name = template_name
                template.description = data.get('description')

                # Handle modality relationship
                modality_name = data.get('modality_name')
                if modality_name:
                    modality = Modality.query.filter_by(modality_name=modality_name).first()
                    if modality:
                        template.modality_id = modality.modality_id
                    else:
                        error_messages.append(f"Modality not found: {modality_name}")

                # Save template first to get ID
                if action == 'add':
                    db.session.add(template)
                    db.session.flush()  # Get the template_id

                # Handle stages
                stages_data = data.get('stages', [])

                # If updating, clear existing template stages
                if action == 'update':
                    TemplateStage.query.filter_by(template_id=template.template_id).delete()

                # Process each stage
                for stage_data in stages_data:
                    stage_name = stage_data.get('stage_name')
                    if not stage_name:
                        continue

                    # Find the process stage
                    process_stage = ProcessStage.query.filter_by(stage_name=stage_name).first()
                    if not process_stage:
                        error_messages.append(f"Process stage not found: {stage_name}")
                        continue

                    # Create template stage link
                    template_stage = TemplateStage(
                        template_id=template.template_id,
                        stage_id=process_stage.stage_id,
                        stage_order=stage_data.get('stage_order', 1),
                        is_required=stage_data.get('is_required', True),
                        base_capabilities=stage_data.get('base_capabilities', [])
                    )
                    db.session.add(template_stage)

                db.session.commit()

                if action == 'add':
                    added_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                failed_count += 1
                error_messages.append(f"Failed to process template {data.get('template_name', 'Unknown')}: {str(e)}")
                db.session.rollback()
                continue

        return {
            'success': True,
            'added_count': added_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
            'error_messages': error_messages
        }

    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'Import failed: {str(e)}',
            'added_count': added_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
            'error_messages': error_messages
        }