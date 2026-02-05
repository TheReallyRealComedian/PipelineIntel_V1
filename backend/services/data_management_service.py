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
    Product, Indication, Challenge, ChallengeModalityDetail, ValueStep,
    ProductSupplyChain, ManufacturingEntity, InternalFacility, ExternalPartner,
    Modality, ProcessStage, ProductTimeline, ProductRegulatoryFiling,
    ProductManufacturingSupplier, User, LLMSettings, ProcessTemplate, TemplateStage,
    ModalityRequirement, ProductRequirement, EntityCapability, ProductProcessOverride,
    ManufacturingCapability,
    # New Core Entities
    DrugSubstance, DrugProduct, Project,
    project_drug_substances, project_drug_products, drug_substance_drug_products
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
    # New Core Entities (insert before products for parallel existence)
    'drug_substances',
    'drug_products',
    'projects',
    # Junction tables for new entities
    'project_drug_substances',
    'project_drug_products',
    'drug_substance_drug_products',
    # Legacy tables (will be removed in future migration)
    'products',
    'indications',
    'value_steps',  # Must come before challenges (FK reference)
    'challenges',
    'challenge_modality_details',
    'llm_settings',
    'template_stages',
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
    # New Core Entities
    'drug_substances': DrugSubstance,
    'drug_products': DrugProduct,
    'projects': Project,
    # Junction tables are handled via db.metadata.tables (not ORM models)
    # Legacy tables
    'products': Product,
    'indications': Indication,
    'value_steps': ValueStep,
    'challenges': Challenge,
    'challenge_modality_details': ChallengeModalityDetail,
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
}


def import_full_database(file_stream):
    """
    Wipes the current database and imports data from a full backup JSON file.
    This is a destructive operation.
    """
    try:
        data = json.load(file_stream)

        if not all(key in data for key in ['users', 'products', 'modalities']):
             return False, "Invalid backup file format. Essential tables are missing."

        db.session.execute(text('SET session_replication_role = replica;'))

        for table_name in reversed(TABLE_IMPORT_ORDER):
            if table_name in data:
                db.session.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;'))

        db.session.commit()

        for table_name in TABLE_IMPORT_ORDER:
            if table_name in data and data[table_name]:
                table_data = data[table_name]
                model_class = MODEL_MAP.get(table_name)

                if model_class:
                    db.session.bulk_insert_mappings(model_class, table_data)
                else:
                    table_obj = db.metadata.tables.get(table_name)
                    if table_obj is not None:
                        db.session.execute(table_obj.insert(), table_data)
                    else:
                        print(f"Warning: Could not find table or model for '{table_name}'. Skipping.")

        db.session.commit()

        db.session.execute(text('SET session_replication_role = DEFAULT;'))
        db.session.commit()

        return True, "Database successfully imported."

    except Exception as e:
        db.session.rollback()
        try:
            db.session.execute(text('SET session_replication_role = DEFAULT;'))
            db.session.commit()
        except:
            pass

        traceback.print_exc()
        return False, f"An error occurred during import: {e}"


def analyze_json_import(json_data: list, model_class, unique_key_field: str):
    """
    Analyzes a list of JSON objects against existing data in the database.
    This function performs the comparison and generates a detailed preview.
    """
    preview_data = []
    try:
        existing_items_query = model_class.query.all()
        existing_items_map = {getattr(item, unique_key_field): item for item in existing_items_query}

        for json_item in json_data:
            entry = {
                'status': 'error',
                'action': 'skip',
                'identifier': None,
                'json_item': json_item,
                'db_item': None,
                'diff': {},
                'messages': []
            }
            identifier = json_item.get(unique_key_field)
            entry['identifier'] = identifier

            if not identifier:
                entry['messages'].append(f"Skipped: Item is missing the unique identifier field '{unique_key_field}'.")
                preview_data.append(entry)
                continue

            existing_item = existing_items_map.get(identifier)

            if existing_item:
                entry['db_item'] = {
                    c.name: getattr(existing_item, c.name)
                    for c in existing_item.__table__.columns
                    if not c.name.startswith('_')
                }

                if model_class == Product:
                    fields_to_check = [key for key in json_item.keys() if hasattr(existing_item, key)]
                    entry['diff'] = _enhanced_field_comparison(existing_item, json_item, fields_to_check)
                else:
                    entry['diff'] = {}
                    for key, new_value in json_item.items():
                        if hasattr(existing_item, key):
                            old_value = getattr(existing_item, key)
                            if str(old_value or '') != str(new_value or ''):
                                entry['diff'][key] = {'old': old_value, 'new': new_value}

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
    missing_keys = defaultdict(set)
    suggestions = {}

    try:
        foreign_key_fields = get_foreign_key_fields(model_class)

        existing_entities = {}
        for field_name, (related_model, lookup_field) in foreign_key_fields.items():
            entities = related_model.query.all()
            existing_entities[field_name] = {
                getattr(entity, lookup_field): entity
                for entity in entities
            }

        for json_item in json_data:
            entry = {
                'status': 'pending_resolution',
                'action': 'add',
                'identifier': json_item.get(unique_key_field),
                'json_item': json_item,
                'missing_foreign_keys': {},
                'messages': []
            }

            has_missing_keys = False
            for field_name, (related_model, lookup_field) in foreign_key_fields.items():
                if field_name in json_item:
                    lookup_value = json_item[field_name]
                    if lookup_value not in existing_entities[field_name]:
                        missing_keys[field_name].add(lookup_value)
                        has_missing_keys = True

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
    from ..models import Product, Modality, ProcessStage, ManufacturingCapability, Challenge, ValueStep

    mappings = {
        Product: {
            'modality_name': (Modality, 'modality_name'),
        },
        Challenge: {
            'value_step': (ValueStep, 'name'),
        },
    }

    return mappings.get(model_class, {})


def generate_suggestions(missing_value, existing_values, max_suggestions=3):
    """
    Generate smart suggestions for missing foreign key values.
    """
    suggestions = []

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


def _resolve_foreign_keys_for_process_stage(item, existing_stages):
    """
    Resolves foreign keys for process stages.
    Converts parent_stage_name to parent_stage_id.
    """
    from ..models import ProcessStage

    resolved_item = item.copy()

    if 'parent_stage_name' in resolved_item:
        parent_stage_name = resolved_item.pop('parent_stage_name')
        if parent_stage_name:
            parent = ProcessStage.query.filter_by(stage_name=parent_stage_name).first()
            if parent:
                resolved_item['parent_stage_id'] = parent.stage_id
            else:
                raise ValueError(f"Parent stage '{parent_stage_name}' not found. Make sure parent stages are imported before child stages.")

    return resolved_item


def _resolve_foreign_keys_for_product(item, existing_products):
    """
    Resolves foreign key references in a product record by name.

    SIMPLIFIED: No longer handles technology or challenge links (schema simplified).
    """
    from ..models import Modality, ProcessTemplate, Product

    resolved = item.copy()
    warnings = []

    # 1. Resolve modality_name → modality_id
    if 'modality_name' in resolved:
        modality_name = resolved.pop('modality_name')
        if modality_name:
            modality = Modality.query.filter_by(modality_name=modality_name).first()
            if modality:
                resolved['modality_id'] = modality.modality_id
                print(f"  ✓ Resolved modality '{modality_name}' → ID {modality.modality_id}")
            else:
                warnings.append(f"Modality '{modality_name}' not found")

    # 2. Resolve process_template_name → process_template_id
    if 'process_template_name' in resolved:
        template_name = resolved.pop('process_template_name')
        if template_name:
            template = ProcessTemplate.query.filter_by(template_name=template_name).first()
            if template:
                if 'modality_id' in resolved and template.modality_id != resolved['modality_id']:
                    modality = Modality.query.get(resolved['modality_id'])
                    warnings.append(
                        f"Template '{template_name}' does not match modality "
                        f"'{modality.modality_name if modality else 'Unknown'}'"
                    )
                else:
                    resolved['process_template_id'] = template.template_id
                    print(f"  ✓ Resolved template '{template_name}' → ID {template.template_id}")
            else:
                available_templates = [t.template_name for t in ProcessTemplate.query.all()]
                warnings.append(f"Process template '{template_name}' not found. Available: {available_templates}")

    # 3. Resolve parent_product_code → parent_product_id
    if 'parent_product_code' in resolved:
        parent_code = resolved.pop('parent_product_code')
        if parent_code:
            parent = Product.query.filter_by(product_code=parent_code).first()

            if not parent:
                for obj in db.session.identity_map.values():
                    if isinstance(obj, Product) and obj.product_code == parent_code:
                        parent = obj
                        break

                if not parent:
                    for obj in db.session.new:
                        if isinstance(obj, Product) and obj.product_code == parent_code:
                            parent = obj
                            break

            if parent:
                if not parent.is_nme:
                    warnings.append(
                        f"Parent product '{parent_code}' is not an NME. "
                        f"Line-Extensions should reference NME products."
                    )
                else:
                    resolved['parent_product_id'] = parent.product_id
                    print(f"  ✓ Resolved parent '{parent_code}' → ID {parent.product_id}")
            else:
                found_in_list = next((p for p in existing_products if p.product_code == parent_code), None)
                if found_in_list:
                    resolved['parent_product_id'] = found_in_list.product_id
                else:
                    warnings.append(f"Parent product '{parent_code}' not found.")

    # 4. Validate Line-Extension logic
    if resolved.get('is_line_extension'):
        if not resolved.get('parent_product_id'):
            warnings.append("Line-Extensions must have a parent_product_id")
        if resolved.get('is_nme'):
            warnings.append("Product cannot be both is_nme=True and is_line_extension=True")

    # 5. Auto-calculate launch_sequence if not provided
    if resolved.get('is_line_extension') and resolved.get('parent_product_id'):
        if 'launch_sequence' not in resolved or not resolved['launch_sequence']:
            db_max = db.session.query(db.func.max(Product.launch_sequence)).filter_by(
                parent_product_id=resolved['parent_product_id']
            ).scalar() or 1

            session_max = 0
            for obj in db.session.identity_map.values():
                if isinstance(obj, Product) and obj.parent_product_id == resolved['parent_product_id']:
                    if obj.launch_sequence and obj.launch_sequence > session_max:
                        session_max = obj.launch_sequence

            resolved['launch_sequence'] = max(db_max, session_max) + 1

    # Remove any obsolete fields that might be in old JSON imports
    for obsolete_field in ['technology_names', 'explicit_challenges', 'excluded_challenges']:
        resolved.pop(obsolete_field, None)

    if warnings:
        resolved['_warnings'] = warnings

    return resolved


def _resolve_foreign_keys_for_challenge(item, existing_challenges):
    """
    Resolves foreign key references in a Challenge record.
    Converts value_step (string name) → value_step_id (FK).
    """
    from ..models import ValueStep

    resolved = item.copy()
    warnings = []

    # Resolve value_step (name) → value_step_id
    if 'value_step' in resolved:
        value_step_name = resolved.pop('value_step')
        if value_step_name:
            vs = ValueStep.query.filter_by(name=value_step_name).first()
            if vs:
                resolved['value_step_id'] = vs.id
                print(f"  ✓ Resolved value_step '{value_step_name}' → ID {vs.id}")
            else:
                # Try fuzzy matching
                all_steps = ValueStep.query.all()
                step_names = [s.name for s in all_steps]
                suggestions = generate_suggestions(value_step_name, step_names, max_suggestions=3)
                if suggestions:
                    suggestion_str = ", ".join([s['value'] for s in suggestions])
                    warnings.append(f"Value step '{value_step_name}' not found. Did you mean: {suggestion_str}?")
                else:
                    warnings.append(f"Value step '{value_step_name}' not found. Available: {', '.join(step_names)}")

    if warnings:
        resolved['_warnings'] = warnings

    return resolved


def _resolve_foreign_keys_for_challenge_modality_detail(item, existing_details):
    """
    Resolves foreign key references in a ChallengeModalityDetail record.
    Converts challenge_name → challenge_id and modality_name → modality_id.
    """
    from ..models import Challenge, Modality

    resolved = item.copy()
    warnings = []

    # 1. Resolve challenge_name → challenge_id
    if 'challenge_name' in resolved:
        challenge_name = resolved.pop('challenge_name')
        if challenge_name:
            challenge = Challenge.query.filter_by(name=challenge_name).first()
            if challenge:
                resolved['challenge_id'] = challenge.id
                print(f"  ✓ Resolved challenge '{challenge_name}' → ID {challenge.id}")
            else:
                warnings.append(f"Challenge '{challenge_name}' not found")

    # 2. Resolve modality_name → modality_id
    if 'modality_name' in resolved:
        modality_name = resolved.pop('modality_name')
        if modality_name:
            modality = Modality.query.filter_by(modality_name=modality_name).first()
            if modality:
                resolved['modality_id'] = modality.modality_id
                print(f"  ✓ Resolved modality '{modality_name}' → ID {modality.modality_id}")
            else:
                warnings.append(f"Modality '{modality_name}' not found")

    # 3. Validate required fields
    if not resolved.get('challenge_id'):
        warnings.append("Missing challenge_id - cannot import without valid challenge reference")
    if not resolved.get('modality_id'):
        warnings.append("Missing modality_id - cannot import without valid modality reference")

    if warnings:
        resolved['_warnings'] = warnings

    return resolved


def _resolve_foreign_keys_for_drug_substance(item, existing_substances):
    """
    Resolves foreign key references in a DrugSubstance record.
    Converts modality_name → modality_id.
    """
    from ..models import Modality

    resolved = item.copy()
    warnings = []

    # Resolve modality_name → modality_id
    if 'modality_name' in resolved:
        modality_name = resolved.pop('modality_name')
        if modality_name:
            modality = Modality.query.filter_by(modality_name=modality_name).first()
            if modality:
                resolved['modality_id'] = modality.modality_id
                print(f"  ✓ Resolved modality '{modality_name}' → ID {modality.modality_id}")
            else:
                warnings.append(f"Modality '{modality_name}' not found")

    if warnings:
        resolved['_warnings'] = warnings

    return resolved


def _resolve_foreign_keys_for_drug_product(item, existing_products):
    """
    Resolves foreign key references in a DrugProduct record.
    DrugProduct has no direct FKs, but we handle M:N links via drug_substance_codes.
    """
    resolved = item.copy()
    warnings = []

    # Note: drug_substance_codes for M:N linking should be handled after creation
    # We just preserve them here for the finalize step
    if 'drug_substance_codes' in resolved:
        # Keep for post-processing, but flag if substances don't exist
        from ..models import DrugSubstance
        codes = resolved.get('drug_substance_codes', [])
        if isinstance(codes, str):
            codes = [c.strip() for c in codes.split(',') if c.strip()]
        for code in codes:
            ds = DrugSubstance.query.filter_by(code=code).first()
            if not ds:
                warnings.append(f"DrugSubstance '{code}' not found for linking")

    if warnings:
        resolved['_warnings'] = warnings

    return resolved


def _resolve_foreign_keys_for_project(item, existing_projects):
    """
    Resolves foreign key references in a Project record.
    Project has no direct FKs, but we handle M:N links via drug_substance_codes and drug_product_codes.
    Also parses date fields.
    """
    resolved = item.copy()
    warnings = []

    # Parse date fields
    date_fields = ['sod', 'dsmm3', 'dsmm4', 'dpmm3', 'dpmm4', 'rofd', 'submission', 'launch']
    for field in date_fields:
        if field in resolved and resolved[field]:
            parsed = _parse_date(resolved[field])
            if parsed:
                resolved[field] = parsed
            else:
                warnings.append(f"Could not parse date for '{field}': {resolved[field]}")

    # Validate M:N links (don't resolve yet, just validate)
    if 'drug_substance_codes' in resolved:
        from ..models import DrugSubstance
        codes = resolved.get('drug_substance_codes', [])
        if isinstance(codes, str):
            codes = [c.strip() for c in codes.split(',') if c.strip()]
        for code in codes:
            ds = DrugSubstance.query.filter_by(code=code).first()
            if not ds:
                warnings.append(f"DrugSubstance '{code}' not found for linking")

    if 'drug_product_codes' in resolved:
        from ..models import DrugProduct
        codes = resolved.get('drug_product_codes', [])
        if isinstance(codes, str):
            codes = [c.strip() for c in codes.split(',') if c.strip()]
        for code in codes:
            dp = DrugProduct.query.filter_by(code=code).first()
            if not dp:
                warnings.append(f"DrugProduct '{code}' not found for linking")

    if warnings:
        resolved['_warnings'] = warnings

    return resolved


def _link_project_relationships(project, raw_data):
    """Create M:N links for Project after creation/update."""
    from ..models import DrugSubstance, DrugProduct

    # Link DrugSubstances
    ds_codes = raw_data.get('drug_substance_codes', [])
    if isinstance(ds_codes, str):
        ds_codes = [c.strip() for c in ds_codes.split(',') if c.strip()]

    for code in ds_codes:
        ds = DrugSubstance.query.filter_by(code=code).first()
        if ds and ds not in project.drug_substances:
            project.drug_substances.append(ds)

    # Link DrugProducts
    dp_codes = raw_data.get('drug_product_codes', [])
    if isinstance(dp_codes, str):
        dp_codes = [c.strip() for c in dp_codes.split(',') if c.strip()]

    for code in dp_codes:
        dp = DrugProduct.query.filter_by(code=code).first()
        if dp and dp not in project.drug_products:
            project.drug_products.append(dp)


def _link_drug_product_relationships(drug_product, raw_data):
    """Create M:N links for DrugProduct after creation/update."""
    from ..models import DrugSubstance

    ds_codes = raw_data.get('drug_substance_codes', [])
    if isinstance(ds_codes, str):
        ds_codes = [c.strip() for c in ds_codes.split(',') if c.strip()]

    for code in ds_codes:
        ds = DrugSubstance.query.filter_by(code=code).first()
        if ds and ds not in drug_product.drug_substances:
            drug_product.drug_substances.append(ds)


def _parse_date(date_string):
    """Helper function to parse date strings into date objects."""
    if not date_string:
        return None

    if isinstance(date_string, date):
        return date_string

    if isinstance(date_string, str):
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

        if field in ['submission_date', 'approval_date', 'ppq_completion_date']:
            json_value = _parse_date(json_value)

        if field in ['regulatory_details', 'ppq_details', 'ds_suppliers', 'dp_suppliers',
                    'device_partners', 'operational_risks', 'timeline_risks',
                    'supply_chain_risks', 'clinical_trials']:
            if json_value is None and existing_value is None:
                continue
            elif json_value != existing_value:
                changed_fields[field] = {'old': existing_value, 'new': json_value}

        elif json_value != existing_value:
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
    """
    try:
        if not hasattr(product_obj, 'product_id') or product_obj.product_id is None:
            print(f"Warning: Product object has no product_id, skipping related tables")
            return

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
        existing_suppliers = ProductManufacturingSupplier.query.filter_by(product_id=product.product_id).count()
        if existing_suppliers > 0:
            return

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


def finalize_import(resolved_data, model_class, unique_key_field, resolver_func=None):
    """
    Finalizes the import by creating or updating database entries.
    Simplified: No longer handles technology or challenge linking.
    """
    from ..models import Product

    success_count = 0
    error_count = 0
    errors = []
    detailed_logs = []

    # Get valid columns for this model to prevent "invalid keyword argument" errors
    valid_columns = set(model_class.get_all_fields())
    # Add manually required fields that might be relationships
    if model_class == Product:
        valid_columns.update(['modality_id', 'process_template_id', 'parent_product_id'])

    header = f"""
{'='*70}
IMPORT PROCESS STARTED
{'='*70}
Entity Type: {model_class.__name__}
Total Items: {len(resolved_data)}
Resolver: {'✓ Enabled' if resolver_func else '✗ None'}
Unique Key: {unique_key_field}
{'='*70}
"""
    print(header)
    detailed_logs.append(header)

    # --- Automatic Sorting for Products ---
    # Ensure NMEs are processed before Line-Extensions
    if model_class == Product:
        print("  → Optimizing import order: NMEs first, then Line Extensions...")

        def product_sort_key(item):
            data = item.get('data') or item.get('json_item') or {}
            # Priority 0: NMEs (is_nme = True) or products without parent_product_code
            # Priority 1: Line Extensions (is_nme = False)
            
            if data.get('is_nme') is True:
                return 0
            if not data.get('parent_product_code'):
                return 0
            return 1

        resolved_data.sort(key=product_sort_key)

        nme_count = sum(1 for item in resolved_data if product_sort_key(item) == 0)
        le_count = len(resolved_data) - nme_count
        print(f"  ✓ Sorted: {nme_count} NMEs will be processed first, then {le_count} Line Extensions")

    try:
        for idx, entry in enumerate(resolved_data, 1):
            item_log = []
            try:
                if 'data' in entry:
                    raw_data = entry['data'].copy()
                elif 'json_item' in entry:
                    raw_data = entry['json_item'].copy()
                else:
                    raise ValueError("Entry missing 'data' or 'json_item' field")

                identifier = raw_data.get(unique_key_field, f"Item {idx}")

                item_header = f"\n[{idx}/{len(resolved_data)}] Processing: {identifier}"
                print(item_header)
                item_log.append(item_header)
                detailed_logs.append(item_header)

                warnings = []

                # 1. Apply Resolver
                data_to_process = raw_data
                if resolver_func:
                    log_msg = f"  → Applying resolver function..."
                    print(log_msg)
                    item_log.append(log_msg)
                    try:
                        existing_instances = model_class.query.all()
                        data_to_process = resolver_func(raw_data, existing_instances)

                        warnings = data_to_process.pop('_warnings', [])

                        log_msg = f"  ✓ Resolver completed"
                        print(log_msg)
                        item_log.append(log_msg)
                        
                        if warnings:
                            for warning in warnings:
                                log_msg = f"  ⚠ Warning: {warning}"
                                print(log_msg)
                                item_log.append(log_msg)
                    except Exception as resolve_error:
                        log_msg = f"  ✗ RESOLVER ERROR: {str(resolve_error)}"
                        print(log_msg)
                        item_log.append(log_msg)
                        raise resolve_error

                # 2. Sanitize Data (Remove fields that don't exist in the model)
                sanitized_data = {k: v for k, v in data_to_process.items() if k in valid_columns}
                
                # 3. Check Existence
                existing_item = model_class.query.filter_by(**{unique_key_field: identifier}).first()

                if existing_item:
                    id_field_name = f"{model_class.__tablename__.replace('manufacturing_', '').rstrip('s')}_id"
                    record_id = getattr(existing_item, id_field_name, 'N/A')
                    log_msg = f"  → Updating existing record (ID: {record_id})"
                    print(log_msg)
                    item_log.append(log_msg)

                    updated_fields = []
                    for key, value in sanitized_data.items():
                        if hasattr(existing_item, key) and getattr(existing_item, key) != value:
                            setattr(existing_item, key, value)
                            updated_fields.append(key)

                    if updated_fields:
                        log_msg = f"  ✓ Updated {len(updated_fields)} fields"
                        print(log_msg)
                        item_log.append(log_msg)
                    
                    item_to_process = existing_item
                else:
                    log_msg = f"  → Creating new record"
                    print(log_msg)
                    item_log.append(log_msg)

                    item_to_process = model_class(**sanitized_data)
                    db.session.add(item_to_process)

                # Commit to allow subsequent items to find this one (important for parent-child relationships)
                db.session.commit()

                # 4. Post-Processing: Create M:N links for Projects
                if model_class == Project:
                    _link_project_relationships(item_to_process, raw_data)
                    db.session.commit()

                # 5. Post-Processing: Create M:N links for DrugProducts
                if model_class == DrugProduct:
                    _link_drug_product_relationships(item_to_process, raw_data)
                    db.session.commit()

                success_count += 1
                log_msg = f"  ✓ SUCCESS"
                print(log_msg)
                item_log.append(log_msg)
                detailed_logs.extend(item_log)

            except Exception as item_error:
                error_count += 1
                db.session.rollback() # Rollback only this item
                error_msg = f"  ✗ ERROR: {str(item_error)}"
                print(error_msg)
                item_log.append(error_msg)
                # Log keys to help debug
                if 'data' in entry:
                     item_log.append(f"  → Data keys: {list(entry['data'].keys())}")
                detailed_logs.extend(item_log)
                errors.append(f"{identifier}: {str(item_error)}")
                continue

        summary = f"""
{'='*70}
IMPORT SUMMARY - {model_class.__name__}
{'='*70}
✓ Success: {success_count}
✗ Errors:  {error_count}
Total:     {len(resolved_data)}
{'='*70}
"""
        print(summary)
        detailed_logs.append(summary)
        
        if errors:
             detailed_logs.append("ERROR DETAILS:")
             detailed_logs.extend([f"  • {e}" for e in errors])

        return {
            "success": True,
            "message": f"Import completed: {success_count} success, {error_count} errors",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors,
            "detailed_logs": detailed_logs
        }

    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": f"Critical Import failure: {str(e)}",
            "detailed_logs": detailed_logs
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
                'action': 'skip',
                'status': 'error',
                'messages': [],
                'diff': {},
                'db_item': None,
                'stage_count': 0
            }

            if not item.get('template_name'):
                preview_item['messages'].append('Missing template_name')
                preview_item['status'] = 'error'
                preview_data.append(preview_item)
                continue

            existing_template = ProcessTemplate.query.filter_by(
                template_name=item['template_name']
            ).first()

            if existing_template:
                preview_item['action'] = 'update'
                preview_item['status'] = 'update'

                preview_item['db_item'] = {
                    'template_name': existing_template.template_name,
                    'description': existing_template.description,
                    'modality_name': existing_template.modality.modality_name if existing_template.modality else None
                }

                preview_item['messages'].append(f'Template exists - will update existing template')
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

            modality_name = item.get('modality_name')
            if modality_name:
                modality = Modality.query.filter_by(modality_name=modality_name).first()
                if not modality:
                    preview_item['messages'].append(f'Modality "{modality_name}" not found')
                    preview_item['status'] = 'needs_resolution'
                    needs_resolution = True

                    if 'modality_name' not in missing_keys:
                        missing_keys['modality_name'] = set()
                    missing_keys['modality_name'].add(modality_name)

                    if 'modality_name' not in suggestions:
                        suggestions['modality_name'] = {}
                    all_modalities = [m.modality_name for m in Modality.query.all()]
                    suggestions['modality_name'][modality_name] = all_modalities[:5]

            stages = item.get('stages', [])
            preview_item['stage_count'] = len(stages)
            stage_issues = []

            for stage_index, stage_item in enumerate(stages):
                stage_name = stage_item.get('stage_name')
                if not stage_name:
                    stage_issues.append(f'Stage {stage_index + 1}: Missing stage_name')
                    continue

                existing_stage = ProcessStage.query.filter_by(stage_name=stage_name).first()
                if not existing_stage:
                    stage_issues.append(f'Stage "{stage_name}" not found in system')
                    preview_item['status'] = 'needs_resolution'
                    needs_resolution = True

                    if 'stage_name' not in missing_keys:
                        missing_keys['stage_name'] = set()
                    missing_keys['stage_name'].add(stage_name)

                    if 'stage_name' not in suggestions:
                        suggestions['stage_name'] = {}
                    all_stages = [s.stage_name for s in ProcessStage.query.all()]
                    suggestions['stage_name'][stage_name] = all_stages[:5]

            if stage_issues:
                preview_item['messages'].extend(stage_issues)

            preview_item['messages'].append(f'Contains {len(stages)} stages')

            if not stage_issues and preview_item['status'] not in ['needs_resolution', 'error']:
                if preview_item['status'] != 'update':
                    preview_item['status'] = 'new'

            preview_data.append(preview_item)

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
    added_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    error_messages = []
    detailed_logs = []

    log_msg = f"\n{'='*60}\nStarting import for Process Templates\nTotal templates to process: {len(resolved_data)}\n{'='*60}"
    print(log_msg)
    detailed_logs.append(log_msg)

    try:
        for idx, entry in enumerate(resolved_data):
            action = entry.get('action')
            data = entry.get('data', {})
            template_name = data.get('template_name', 'Unknown')

            log_msg = f"[{idx+1}/{len(resolved_data)}] Processing: {template_name}"
            print(log_msg)
            detailed_logs.append(log_msg)

            if action == 'skip':
                skipped_count += 1
                log_msg = f"  → Skipped by user"
                print(log_msg)
                detailed_logs.append(log_msg)
                continue

            try:
                modality_name = data.get('modality_name')
                if not modality_name:
                    raise ValueError("modality_name is required")

                log_msg = f"  → Resolving modality: {modality_name}"
                print(log_msg)
                detailed_logs.append(log_msg)

                modality = Modality.query.filter_by(modality_name=modality_name).first()
                if not modality:
                    raise ValueError(f"Modality '{modality_name}' not found")

                log_msg = f"  ✓ Modality resolved: {modality.modality_name} (ID: {modality.modality_id})"
                print(log_msg)
                detailed_logs.append(log_msg)

                existing_template = ProcessTemplate.query.filter_by(
                    template_name=template_name
                ).first()

                if action == 'update' and existing_template:
                    log_msg = f"  → Updating existing template"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                    template = existing_template
                    template.modality_id = modality.modality_id
                    template.description = data.get('description', '')

                    old_stage_count = TemplateStage.query.filter_by(
                        template_id=template.template_id
                    ).delete()

                    log_msg = f"  → Removed {old_stage_count} old stages"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                elif action == 'add':
                    log_msg = f"  → Creating new template"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                    template = ProcessTemplate(
                        template_name=template_name,
                        modality_id=modality.modality_id,
                        description=data.get('description', '')
                    )
                    db.session.add(template)
                    db.session.flush()

                    log_msg = f"  ✓ Template created (ID: {template.template_id})"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                stages = data.get('stages', [])
                log_msg = f"  → Processing {len(stages)} stages"
                print(log_msg)
                detailed_logs.append(log_msg)

                for stage_idx, stage_data in enumerate(stages):
                    stage_name = stage_data.get('stage_name')
                    log_msg = f"    [{stage_idx+1}/{len(stages)}] Stage: {stage_name}"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                    process_stage = ProcessStage.query.filter_by(
                        stage_name=stage_name
                    ).first()

                    if not process_stage:
                        raise ValueError(f"Stage '{stage_name}' not found")

                    template_stage = TemplateStage(
                        template_id=template.template_id,
                        stage_id=process_stage.stage_id,
                        stage_order=stage_data.get('stage_order', stage_idx + 1),
                        is_required=stage_data.get('is_required', True),
                        base_capabilities=stage_data.get('base_capabilities', [])
                    )
                    db.session.add(template_stage)

                    log_msg = f"      ✓ Stage linked (Order: {template_stage.stage_order})"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                db.session.commit()
                log_msg = f"  ✓ Template completed successfully"
                print(log_msg)
                detailed_logs.append(log_msg)

                if action == 'add':
                    added_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to process template '{template_name}': {str(e)}"
                error_messages.append(error_msg)
                log_msg = f"  ✗ ERROR: {str(e)}"
                print(log_msg)
                detailed_logs.append(log_msg)
                db.session.rollback()
                continue

        summary = f"\n{'='*60}\nImport Summary for Process Templates\nAdded: {added_count}\nUpdated: {updated_count}\nSkipped: {skipped_count}\nFailed: {failed_count}\n{'='*60}"
        print(summary)
        detailed_logs.append(summary)

        if error_messages:
            error_details_header = "\nError Details:"
            print(error_details_header)
            detailed_logs.append(error_details_header)
            for error in error_messages:
                log_msg = f"  - {error}"
                print(log_msg)
                detailed_logs.append(log_msg)

        return {
            'success': True,
            'message': f"Import completed: {added_count} added, {updated_count} updated, {failed_count} errors",
            'added_count': added_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
            'error_messages': error_messages,
            'success_count': added_count + updated_count,
            'detailed_logs': detailed_logs
        }

    except Exception as e:
        db.session.rollback()
        log_msg = f"\n✗ CRITICAL ERROR: {str(e)}"
        print(log_msg)
        detailed_logs.append(log_msg)
        return {
            'success': False,
            'message': f'Import failed: {str(e)}',
            'added_count': added_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
            'error_messages': error_messages + [str(e)],
            'detailed_logs': detailed_logs
        }


def analyze_challenge_modality_details_import(json_data):
    """
    Analyze challenge modality details import data.
    Uses challenge_name + modality_name as composite identifier.
    """
    from ..models import Challenge, Modality, ChallengeModalityDetail

    try:
        preview_data = []
        missing_keys = {}
        suggestions = {}
        needs_resolution = False

        # Build lookup maps
        challenges = {c.name: c for c in Challenge.query.all()}
        modalities = {m.modality_name: m for m in Modality.query.all()}

        for index, item in enumerate(json_data):
            challenge_name = item.get('challenge_name', '')
            modality_name = item.get('modality_name', '')
            identifier = f"{challenge_name} | {modality_name}"

            preview_item = {
                'index': index,
                'json_item': item,
                'identifier': identifier,
                'action': 'skip',
                'status': 'error',
                'messages': [],
                'diff': {},
                'db_item': None,
                'missing_foreign_keys': {}  # Required by template
            }

            # Validate challenge_name
            if not challenge_name:
                preview_item['messages'].append('Missing challenge_name')
                preview_item['status'] = 'error'
                preview_data.append(preview_item)
                continue

            # Validate modality_name
            if not modality_name:
                preview_item['messages'].append('Missing modality_name')
                preview_item['status'] = 'error'
                preview_data.append(preview_item)
                continue

            # Check if challenge exists
            challenge = challenges.get(challenge_name)
            if not challenge:
                preview_item['messages'].append(f'Challenge "{challenge_name}" not found')
                preview_item['status'] = 'needs_resolution'
                preview_item['missing_foreign_keys']['challenge_name'] = challenge_name
                needs_resolution = True

                if 'challenge_name' not in missing_keys:
                    missing_keys['challenge_name'] = set()
                missing_keys['challenge_name'].add(challenge_name)

                if 'challenge_name' not in suggestions:
                    suggestions['challenge_name'] = {}
                # Generate suggestions in the format expected by template
                suggestions['challenge_name'][challenge_name] = generate_suggestions(
                    challenge_name, list(challenges.keys())
                )

            # Check if modality exists
            modality = modalities.get(modality_name)
            if not modality:
                preview_item['messages'].append(f'Modality "{modality_name}" not found')
                preview_item['status'] = 'needs_resolution'
                preview_item['missing_foreign_keys']['modality_name'] = modality_name
                needs_resolution = True

                if 'modality_name' not in missing_keys:
                    missing_keys['modality_name'] = set()
                missing_keys['modality_name'].add(modality_name)

                if 'modality_name' not in suggestions:
                    suggestions['modality_name'] = {}
                # Generate suggestions in the format expected by template
                suggestions['modality_name'][modality_name] = generate_suggestions(
                    modality_name, list(modalities.keys())
                )

            # If both exist, check for existing detail record
            if challenge and modality:
                existing_detail = ChallengeModalityDetail.query.filter_by(
                    challenge_id=challenge.id,
                    modality_id=modality.modality_id
                ).first()

                if existing_detail:
                    preview_item['action'] = 'update'
                    preview_item['status'] = 'update'
                    preview_item['db_item'] = {
                        'id': existing_detail.id,
                        'impact_score': existing_detail.impact_score,
                        'maturity_score': existing_detail.maturity_score
                    }
                    preview_item['messages'].append('Record exists - will update')
                else:
                    preview_item['action'] = 'add'
                    preview_item['status'] = 'new'
                    preview_item['messages'].append('New record - will be created')

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
            'total_items': len(json_data)
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Analysis failed: {str(e)}'
        }


def finalize_challenge_modality_details_import(resolved_data):
    """
    Finalize the import of challenge modality details.
    """
    from ..models import Challenge, Modality, ChallengeModalityDetail

    added_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    error_messages = []
    detailed_logs = []

    log_msg = f"\n{'='*60}\nStarting import for Challenge Modality Details\nTotal items: {len(resolved_data)}\n{'='*60}"
    print(log_msg)
    detailed_logs.append(log_msg)

    # Build lookup maps
    challenges = {c.name: c for c in Challenge.query.all()}
    modalities = {m.modality_name: m for m in Modality.query.all()}

    try:
        for idx, entry in enumerate(resolved_data):
            action = entry.get('action')
            data = entry.get('data', {})

            challenge_name = data.get('challenge_name', '')
            modality_name = data.get('modality_name', '')
            identifier = f"{challenge_name} | {modality_name}"

            log_msg = f"[{idx+1}/{len(resolved_data)}] Processing: {identifier}"
            print(log_msg)
            detailed_logs.append(log_msg)

            if action == 'skip':
                skipped_count += 1
                log_msg = f"  → Skipped by user"
                print(log_msg)
                detailed_logs.append(log_msg)
                continue

            try:
                # Resolve foreign keys
                challenge = challenges.get(challenge_name)
                modality = modalities.get(modality_name)

                if not challenge:
                    raise ValueError(f"Challenge '{challenge_name}' not found")
                if not modality:
                    raise ValueError(f"Modality '{modality_name}' not found")

                # Always check for existing record to avoid duplicates
                existing_detail = ChallengeModalityDetail.query.filter_by(
                    challenge_id=challenge.id,
                    modality_id=modality.modality_id
                ).first()

                if existing_detail:
                    # Update existing record
                    log_msg = f"  → Updating existing record (ID: {existing_detail.id})"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                    # Update fields
                    if 'specific_description' in data:
                        existing_detail.specific_description = data['specific_description']
                    if 'specific_root_cause' in data:
                        existing_detail.specific_root_cause = data['specific_root_cause']
                    if 'impact_score' in data:
                        existing_detail.impact_score = data['impact_score']
                    if 'impact_details' in data:
                        existing_detail.impact_details = data['impact_details']
                    if 'maturity_score' in data:
                        existing_detail.maturity_score = data['maturity_score']
                    if 'maturity_details' in data:
                        existing_detail.maturity_details = data['maturity_details']
                    if 'trends_3_5_years' in data:
                        existing_detail.trends_3_5_years = data['trends_3_5_years']

                    updated_count += 1

                else:
                    # Create new record
                    log_msg = f"  → Creating new record"
                    print(log_msg)
                    detailed_logs.append(log_msg)

                    new_detail = ChallengeModalityDetail(
                        challenge_id=challenge.id,
                        modality_id=modality.modality_id,
                        specific_description=data.get('specific_description'),
                        specific_root_cause=data.get('specific_root_cause'),
                        impact_score=data.get('impact_score'),
                        impact_details=data.get('impact_details'),
                        maturity_score=data.get('maturity_score'),
                        maturity_details=data.get('maturity_details'),
                        trends_3_5_years=data.get('trends_3_5_years')
                    )
                    db.session.add(new_detail)
                    added_count += 1

                db.session.commit()
                log_msg = f"  ✓ SUCCESS"
                print(log_msg)
                detailed_logs.append(log_msg)

            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to process '{identifier}': {str(e)}"
                error_messages.append(error_msg)
                log_msg = f"  ✗ ERROR: {str(e)}"
                print(log_msg)
                detailed_logs.append(log_msg)
                db.session.rollback()
                continue

        summary = f"\n{'='*60}\nImport Summary for Challenge Modality Details\nAdded: {added_count}\nUpdated: {updated_count}\nSkipped: {skipped_count}\nFailed: {failed_count}\n{'='*60}"
        print(summary)
        detailed_logs.append(summary)

        return {
            'success': True,
            'message': f"Import completed: {added_count} added, {updated_count} updated, {failed_count} errors",
            'added_count': added_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
            'error_messages': error_messages,
            'success_count': added_count + updated_count,
            'detailed_logs': detailed_logs
        }

    except Exception as e:
        db.session.rollback()
        log_msg = f"\n✗ CRITICAL ERROR: {str(e)}"
        print(log_msg)
        detailed_logs.append(log_msg)
        return {
            'success': False,
            'message': f'Import failed: {str(e)}',
            'detailed_logs': detailed_logs
        }