# backend/services/export_service.py
import json
import tiktoken
from sqlalchemy.orm import Session
from . import product_service, indication_service, challenge_service, technology_service


# Define a map of entities that can be exported
# This makes the service easily extensible in the future
EXPORTABLE_ENTITIES = {
    'products': {
        'model': product_service.Product,
        'fetch_all_func': product_service.get_all_products
    },
    'indications': {
        'model': indication_service.Indication,
        'fetch_all_func': indication_service.get_all_indications
    },
    'challenges': {
        'model': challenge_service.ManufacturingChallenge,
        'fetch_all_func': challenge_service.get_all_challenges
    },
    'technologies': {
        'model': technology_service.ManufacturingTechnology,
        'fetch_all_func': technology_service.get_all_technologies
    }
}

def count_tokens(text: str) -> int:
    """Counts tokens in a string using tiktoken."""
    try:
        # Use a common encoding that works for many models
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback for any errors: approximate count
        return len(text) // 4

def prepare_json_export(db_session: Session, form_data: dict):
    """
    Prepares a custom JSON export based on user selections from the form.
    """
    final_json_data = {}
    
    # Iterate over all entities that can be exported
    for entity_name, config in EXPORTABLE_ENTITIES.items():
        
        # Check if any fields for this entity were selected
        selected_fields = form_data.getlist(f'{entity_name}_fields')
        if not selected_fields:
            continue

        # Get the list of selected IDs for this entity
        selected_ids = [int(id_str) for id_str in form_data.getlist(f'{entity_name}_ids') if id_str.isdigit()]

        # Build the query
        query = db_session.query(config['model'])
        if selected_ids:
            # The primary key for each model is named differently (e.g., product_id, indication_id)
            pk_column = config['model'].__mapper__.primary_key[0]
            query = query.filter(pk_column.in_(selected_ids))

        # Execute the query and serialize the data
        results = query.all()
        entity_data_list = []
        for item in results:
            item_data = {}
            for field in selected_fields:
                if hasattr(item, field):
                    item_data[field] = getattr(item, field)
            entity_data_list.append(item_data)
        
        if entity_data_list:
            final_json_data[entity_name] = entity_data_list

    # Calculate token count for the final JSON string
    json_string = json.dumps(final_json_data, default=str, indent=2)
    total_tokens = count_tokens(json_string)

    return json_string, total_tokens