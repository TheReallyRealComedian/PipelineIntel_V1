# backend/services/data_management_service.py
import json
import traceback
from sqlalchemy.orm import Session
from ..models import Product, Indication, ManufacturingChallenge, ManufacturingTechnology, Partner, ProductSupplyChain

def analyze_json_import(db_session: Session, json_data: list, model_class, unique_key_field: str):
    """
    Analyzes a list of JSON objects against existing data in the database.
    This function performs the comparison and generates a detailed preview.
    """
    preview_data = []
    try:
        # --- MODIFICATION START: Pre-fetch product map for challenge analysis ---
        product_map = {p.product_code: p for p in db_session.query(Product).all()} if model_class == ManufacturingChallenge else {}
        # --- MODIFICATION END ---
        
        existing_items_query = db_session.query(model_class).all()
        existing_items_map = {getattr(item, unique_key_field): item for item in existing_items_query}
        
        for json_item in json_data:
            entry = { 'status': 'error', 'action': 'skip', 'identifier': None, 'json_item': json_item, 'db_item': None, 'diff': {}, 'messages': [] }
            identifier = json_item.get(unique_key_field)
            entry['identifier'] = identifier

            if not identifier:
                entry['messages'].append(f"Skipped: Item is missing the unique identifier field '{unique_key_field}'.")
                preview_data.append(entry)
                continue

            # --- MODIFICATION START: Handle product links for challenges ---
            product_codes_from_json = set()
            if model_class == ManufacturingChallenge:
                # Pop the product_codes so it's not treated as a regular field diff
                product_codes_from_json = set(json_item.pop('product_codes', []))
                
                invalid_codes = [code for code in product_codes_from_json if code not in product_map]
                if invalid_codes:
                    entry['messages'].append(f"Warning: The following product codes were not found and will be ignored: {', '.join(invalid_codes)}")
                
                # Use only valid codes for comparison
                product_codes_from_json = {code for code in product_codes_from_json if code in product_map}
            # --- MODIFICATION END ---

            existing_item = existing_items_map.get(identifier)

            if existing_item:
                entry['db_item'] = {c.name: getattr(existing_item, c.name) for c in existing_item.__table__.columns if not c.name.startswith('_')}
                is_dirty = False
                
                for key, new_value in json_item.items():
                    if hasattr(existing_item, key):
                        old_value = getattr(existing_item, key)
                        if str(old_value or '') != str(new_value or ''):
                            is_dirty = True
                            entry['diff'][key] = {'old': old_value, 'new': new_value}
                
                # --- MODIFICATION START: Compare product links for challenges ---
                if model_class == ManufacturingChallenge:
                    current_product_codes = {p.product_code for p in existing_item.products}
                    added = product_codes_from_json - current_product_codes
                    removed = current_product_codes - product_codes_from_json
                    if added or removed:
                        is_dirty = True
                        entry['diff']['product_links'] = {
                            'added': sorted(list(added)),
                            'removed': sorted(list(removed))
                        }
                # --- MODIFICATION END ---
                
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
                # --- MODIFICATION START: Show products for new challenges ---
                if model_class == ManufacturingChallenge and product_codes_from_json:
                     entry['diff']['product_links'] = {'added': sorted(list(product_codes_from_json)), 'removed': []}
                # --- MODIFICATION END ---
            
            preview_data.append(entry)
        
        return {"success": True, "preview_data": preview_data}
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "message": f"An unexpected analysis error occurred: {e}"}

def finalize_import(db_session: Session, resolved_data: list, model_class, unique_key_field: str):
    """
    Takes user-approved changes from the preview and commits them to the DB.
    """
    added_count, updated_count, skipped_count, failed_count = 0, 0, 0, 0
    error_messages = []

    product_map = {p.product_code: p for p in db_session.query(Product).all()}
    partner_map = {p.partner_name: p.partner_id for p in db_session.query(Partner.partner_name, Partner.partner_id).all()}

    for item in resolved_data:
        action = item.get('action')
        data = item.get('data')
        identifier = data.get(unique_key_field)

        if action == 'skip':
            skipped_count += 1
            continue

        try:
            # --- MODIFICATION START: Pop product_codes before object creation/update ---
            product_codes_to_link = []
            if model_class == ManufacturingChallenge:
                product_codes_to_link = data.pop('product_codes', [])
            # --- MODIFICATION END ---
            
            if model_class == Indication:
                product_code = data.pop('product_code', None)
                if product_code and product_code in product_map:
                    data['product_id'] = product_map[product_code].product_id
                else:
                    raise ValueError(f"Parent Product with code '{product_code}' not found.")

            if model_class == ProductSupplyChain:
                product_code = data.pop('product_code', None)
                partner_name = data.pop('partner_name', None)
                if product_code and product_code in product_map:
                    data['product_id'] = product_map[product_code].product_id
                else:
                    raise ValueError(f"Parent Product with code '{product_code}' not found for supply chain.")
                if partner_name and partner_name in partner_map:
                    data['partner_id'] = partner_map[partner_name]
                elif partner_name:
                     raise ValueError(f"Partner with name '{partner_name}' not found for supply chain.")

            if action == 'add':
                new_obj = model_class(**data)
                db_session.add(new_obj)
                added_count += 1
                # --- MODIFICATION START: Link products for new challenges ---
                if model_class == ManufacturingChallenge and product_codes_to_link:
                    valid_products = [product_map[code] for code in product_codes_to_link if code in product_map]
                    new_obj.products = valid_products
                # --- MODIFICATION END ---

            elif action == 'update':
                obj_to_update = db_session.query(model_class).filter(getattr(model_class, unique_key_field) == identifier).first()
                if obj_to_update:
                    for key, value in data.items():
                        setattr(obj_to_update, key, value)
                    updated_count += 1
                    # --- MODIFICATION START: Update product links for existing challenges ---
                    if model_class == ManufacturingChallenge:
                        valid_products = [product_map[code] for code in product_codes_to_link if code in product_map]
                        obj_to_update.products = valid_products # SQLAlchemy handles the association changes
                    # --- MODIFICATION END ---
                else:
                    raise ValueError(f"Could not find existing item with identifier '{identifier}' to update.")

        except Exception as e:
            failed_count += 1
            error_messages.append(f"Failed to process '{identifier}': {e}")
            db_session.rollback()
    
    if failed_count > 0:
        return {"success": False, "message": f"Import finished with {failed_count} errors. No changes from the failed items were saved.", "log": error_messages}
    
    db_session.commit()
    return {"success": True, "message": f"Import successful! Added: {added_count}, Updated: {updated_count}, Skipped: {skipped_count}."}