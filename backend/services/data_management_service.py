# backend/services/data_management_service.py
import json
import traceback
import difflib
from collections import defaultdict
from datetime import datetime, date
import re

from ..db import db
from ..models import (
    Product, Indication, ManufacturingChallenge, ManufacturingTechnology,
    ProductSupplyChain, ManufacturingEntity, InternalFacility, ExternalPartner,
    Modality, ProcessStage, ProductTimeline, ProductRegulatoryFiling,
    ProductManufacturingSupplier
)


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


def finalize_import(resolved_data: list, model_class, unique_key_field: str):
    """
    Takes user-approved changes from the preview and commits them to the DB.
    CORRECTED VERSION: Properly handles Product imports with related table data.
    """
    from ..db import db
    from ..models import (
        Product, Indication, ManufacturingChallenge, ManufacturingTechnology,
        ProductSupplyChain, ProcessStage, InternalFacility, ExternalPartner,
        ManufacturingEntity, Modality, ProductTimeline, ProductRegulatoryFiling, ProductManufacturingSupplier
    )

    added_count, updated_count, skipped_count, failed_count = 0, 0, 0, 0
    error_messages = []

    # Pre-fetch maps for foreign key lookups
    product_map = {p.product_code: p for p in Product.query.all()}
    modality_map = {m.modality_name: m.modality_id for m in Modality.query.with_entities(Modality.modality_name, Modality.modality_id).all()}
    stage_map = {s.stage_name: s.stage_id for s in ProcessStage.query.with_entities(ProcessStage.stage_name, ProcessStage.stage_id).all()}
    entity_map = {e.entity_name: e.entity_id for e in ManufacturingEntity.query.with_entities(ManufacturingEntity.entity_name, ManufacturingEntity.entity_id).all()}

    # Sort ProcessStage imports by hierarchy level
    if model_class == ProcessStage:
        resolved_data = sorted(resolved_data, key=lambda item: item.get('data', {}).get('hierarchy_level', 999))

    for item in resolved_data:
        action = item.get('action')
        data_dict = item.get('data', {})  # Keep original for related tables
        identifier = data_dict.get(unique_key_field)

        if action == 'skip':
            skipped_count += 1
            continue

        try:
            # ==================== SPECIAL HANDLING FOR PRODUCTS ====================
            if model_class == Product:
                # Separate main product data from related table data
                main_data, related_data = _separate_product_data(data_dict)
                data = main_data.copy()  # Use only main data for Product creation

                # Handle modality lookup
                modality_name = data.pop('modality_name', None)
                if modality_name and modality_name in modality_map:
                    data['modality_id'] = modality_map[modality_name]
                elif modality_name:
                    raise ValueError(f"Modality '{modality_name}' not found.")

                if action == 'add':
                    new_obj = Product(**data)
                    db.session.add(new_obj)
                    db.session.flush()  # Get the product_id
                    added_count += 1

                    # Update product_map for potential later use
                    product_map[new_obj.product_code] = new_obj

                    # Process related tables
                    try:
                        _process_product_related_tables(new_obj, related_data)
                    except Exception as e:
                        print(f"Warning: Failed to process related tables for {new_obj.product_code}: {e}")

                elif action == 'update':
                    obj_to_update = Product.query.filter(getattr(Product, unique_key_field) == identifier).first()
                    if obj_to_update:
                        for key, value in data.items():
                            setattr(obj_to_update, key, value)
                        updated_count += 1

                        # Process related tables for updated product
                        try:
                            _process_product_related_tables(obj_to_update, related_data)
                        except Exception as e:
                            print(f"Warning: Failed to process related tables for {obj_to_update.product_code}: {e}")
                    else:
                        raise ValueError(f"Could not find existing product with identifier '{identifier}' to update.")

            # ==================== HANDLE OTHER MODEL TYPES ====================
            else:
                data = data_dict.copy()
                product_codes_to_link = []

                if model_class == ManufacturingChallenge:
                    product_codes_to_link = data.pop('product_codes', [])

                # Handle foreign key lookups by name
                if model_class == ManufacturingTechnology:
                    stage_name = data.pop('stage_name', None)
                    if stage_name and stage_name in stage_map:
                        data['stage_id'] = stage_map[stage_name]
                    elif stage_name:
                        raise ValueError(f"Process Stage '{stage_name}' not found.")

                # Handle ProcessStage hierarchy
                if model_class == ProcessStage:
                    parent_stage_name = data.pop('parent_stage_name', None)
                    if parent_stage_name:
                        if parent_stage_name in stage_map:
                            data['parent_stage_id'] = stage_map[parent_stage_name]
                        else:
                            raise ValueError(f"Parent stage '{parent_stage_name}' not found.")

                # Handle ManufacturingChallenge stage link
                if model_class == ManufacturingChallenge:
                    primary_stage_name = data.pop('primary_stage_name', None)
                    if primary_stage_name:
                        if primary_stage_name in stage_map:
                            data['primary_stage_id'] = stage_map[primary_stage_name]
                        else:
                            raise ValueError(f"Primary stage '{primary_stage_name}' not found.")

                if model_class == Indication:
                    product_code = data.pop('product_code', None)
                    if product_code and product_code in product_map:
                        data['product_id'] = product_map[product_code].product_id
                    else:
                        raise ValueError(f"Parent Product with code '{product_code}' not found.")

                # Handle supply chain logic
                if model_class == ProductSupplyChain:
                    product_code = data.pop('product_code', None)
                    entity_name = data.pop('entity_name', None)
                    if product_code and product_code in product_map:
                        data['product_id'] = product_map[product_code].product_id
                    else:
                        raise ValueError(f"Parent Product with code '{product_code}' not found for supply chain.")
                    if entity_name and entity_name in entity_map:
                        data['entity_id'] = entity_map[entity_name]
                    elif entity_name:
                        raise ValueError(f"Manufacturing Entity with name '{entity_name}' not found for supply chain.")

                # Create or update the object
                if action == 'add':
                    if model_class in [InternalFacility, ExternalPartner]:
                        base_entity_data = {
                            'entity_name': data.get('facility_code') if model_class == InternalFacility else data.get('company_name'),
                            'entity_type': 'Internal' if model_class == InternalFacility else 'External',
                            'location': data.pop('location', None),
                            'operational_status': data.pop('operational_status', None)
                        }
                        if not base_entity_data['entity_name']:
                            raise ValueError(f"Unique identifier '{unique_key_field}' is required.")

                        base_entity = ManufacturingEntity(**base_entity_data)
                        db.session.add(base_entity)
                        db.session.flush()

                        data['entity_id'] = base_entity.entity_id
                        new_obj = model_class(**data)
                    else:
                        new_obj = model_class(**data)

                    db.session.add(new_obj)
                    added_count += 1

                    if model_class == ProcessStage:
                        db.session.flush()
                        stage_map[new_obj.stage_name] = new_obj.stage_id

                    if model_class == ManufacturingChallenge and product_codes_to_link:
                        valid_products = [product_map[code] for code in product_codes_to_link if code in product_map]
                        new_obj.products = valid_products

                elif action == 'update':
                    obj_to_update = model_class.query.filter(getattr(model_class, unique_key_field) == identifier).first()
                    if obj_to_update:
                        if model_class in [InternalFacility, ExternalPartner]:
                            base_entity = ManufacturingEntity.query.get(obj_to_update.entity_id)
                            base_entity.location = data.pop('location', base_entity.location)
                            base_entity.operational_status = data.pop('operational_status', base_entity.operational_status)
                            base_entity.entity_name = data.get('facility_code', base_entity.entity_name) if model_class == InternalFacility else data.get('company_name', base_entity.entity_name)

                        for key, value in data.items():
                            setattr(obj_to_update, key, value)
                        updated_count += 1

                        if model_class == ManufacturingChallenge:
                            valid_products = [product_map[code] for code in product_codes_to_link if code in product_map]
                            obj_to_update.products = valid_products
                    else:
                        raise ValueError(f"Could not find existing item with identifier '{identifier}' to update.")

        except Exception as e:
            failed_count += 1
            error_messages.append(f"Failed to process '{identifier}': {e}")
            print(f"Import error for {identifier}: {e}")
            import traceback
            traceback.print_exc()

    if failed_count > 0:
        db.session.rollback()
        return {"success": False, "message": f"Import finished with {failed_count} errors. No changes were saved.", "log": error_messages}

    db.session.commit()
    return {"success": True, "message": f"Import successful! Added: {added_count}, Updated: {updated_count}, Skipped: {skipped_count}."}