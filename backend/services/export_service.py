# backend/services/export_service.py
import json
import tiktoken

from ..db import db

# NOTE: We are removing the direct service imports from the top level.
# They will be imported locally within a helper function to avoid circular dependencies.


def _get_exportable_entities():
    """
    A helper function to build the EXPORTABLE_ENTITIES dictionary.
    Imports are done locally within the function to prevent circular import errors at startup.
    """
    # These imports are now safe because they only run when this function is called.
    from . import (
        product_service,
        indication_service,
        challenge_service,
        technology_service,
        modality_service,
        facility_service,
        capability_service,
    )
    from ..models import (
        Modality,
        ManufacturingEntity,
        ManufacturingCapability,
        Product,
        Indication,
        ManufacturingChallenge,
        ManufacturingTechnology,
        ProductTimeline,
        ProductRegulatoryFiling,
        ProductManufacturingSupplier,
    )

    return {
        "products": {
            "model": Product,
            "fetch_all_func": product_service.get_all_products,
            "pk_field": "product_id",
            "name_field": "product_name",
        },
        "indications": {
            "model": Indication,
            "fetch_all_func": indication_service.get_all_indications,
            "pk_field": "indication_id",
            "name_field": "indication_name",
        },
        "challenges": {
            "model": ManufacturingChallenge,
            "fetch_all_func": challenge_service.get_all_challenges,
            "pk_field": "challenge_id",
            "name_field": "challenge_name",
        },
        "technologies": {
            "model": ManufacturingTechnology,
            "fetch_all_func": technology_service.get_all_technologies,
            "pk_field": "technology_id",
            "name_field": "technology_name",
        },
        "modalities": {
            "model": Modality,
            "fetch_all_func": modality_service.get_all_modalities,
            "pk_field": "modality_id",
            "name_field": "modality_name",
        },
        "facilities": {
            "model": ManufacturingEntity,
            "fetch_all_func": facility_service.get_all_entities,
            "pk_field": "entity_id",
            "name_field": "entity_name",
        },
        "capabilities": {
            "model": ManufacturingCapability,
            "fetch_all_func": capability_service.get_all_capabilities,
            "pk_field": "capability_id",
            "name_field": "capability_name",
        },
        "product_timelines": {
            "model": ProductTimeline,
            "fetch_all_func": lambda: ProductTimeline.query.all(),
            "pk_field": "timeline_id",
            "name_field": "milestone_name",
        },
        "product_regulatory_filings": {
            "model": ProductRegulatoryFiling,
            "fetch_all_func": lambda: ProductRegulatoryFiling.query.all(),
            "pk_field": "filing_id",
            "name_field": "indication",
        },
        "product_manufacturing_suppliers": {
            "model": ProductManufacturingSupplier,
            "fetch_all_func": lambda: ProductManufacturingSupplier.query.all(),
            "pk_field": "supplier_id",
            "name_field": "supplier_name",
        },
    }


def get_export_page_context():
    """Gathers all necessary data for rendering the data export page."""
    EXPORTABLE_ENTITIES = _get_exportable_entities()

    all_items = {
        name: config["fetch_all_func"]()
        for name, config in EXPORTABLE_ENTITIES.items()
    }

    selectable_fields = {
        name: config["model"].get_all_fields()
        for name, config in EXPORTABLE_ENTITIES.items()
    }

    display_config = {
        name: {"pk": config["pk_field"], "name": config["name_field"]}
        for name, config in EXPORTABLE_ENTITIES.items()
    }

    return {
        "all_items": all_items,
        "selectable_fields": selectable_fields,
        "display_config": display_config,
    }


def count_tokens(text: str) -> int:
    """Counts tokens in a string using tiktoken."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return len(text) // 4


def prepare_json_export(form_data: dict):
    """Prepares a custom JSON export based on user selections from the form."""
    EXPORTABLE_ENTITIES = _get_exportable_entities()
    final_json_data = {}

    for entity_name, config in EXPORTABLE_ENTITIES.items():
        selected_fields = form_data.getlist(f"{entity_name}_fields")
        if not selected_fields:
            continue

        selected_ids = [
            int(id_str)
            for id_str in form_data.getlist(f"{entity_name}_ids")
            if id_str.isdigit()
        ]

        query = config["model"].query
        if selected_ids:
            pk_column = getattr(config["model"], config["pk_field"])
            query = query.filter(pk_column.in_(selected_ids))

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

    json_string = json.dumps(final_json_data, default=str, indent=2)
    total_tokens = count_tokens(json_string)

    return json_string, total_tokens