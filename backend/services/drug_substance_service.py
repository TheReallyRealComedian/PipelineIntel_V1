# backend/services/drug_substance_service.py
from sqlalchemy.orm import joinedload
from ..db import db
from ..models import DrugSubstance, Modality


def get_all_drug_substances():
    """Retrieves all drug substances, ordered by code."""
    return DrugSubstance.query.options(
        joinedload(DrugSubstance.modality)
    ).order_by(DrugSubstance.code).all()


def get_drug_substance_by_id(ds_id: int):
    """Retrieves a single drug substance by ID with relationships."""
    return DrugSubstance.query.options(
        joinedload(DrugSubstance.modality),
        joinedload(DrugSubstance.projects),
        joinedload(DrugSubstance.drug_products)
    ).get(ds_id)


def get_drug_substance_by_code(code: str):
    """Retrieves a single drug substance by code."""
    return DrugSubstance.query.filter_by(code=code).first()


def get_drug_substance_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic drug substances table."""
    DEFAULT_COLUMNS = ['code', 'inn', 'molecule_type', 'development_approach', 'demand_category', 'status']

    all_fields = DrugSubstance.get_all_fields()

    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    drug_substances = get_all_drug_substances()

    # Convert SQLAlchemy objects to dictionaries for the template
    ds_dicts = []
    for ds in drug_substances:
        ds_dict = {field: getattr(ds, field) for field in all_fields}
        # Add modality name for display
        ds_dict['modality_name'] = ds.modality.modality_name if ds.modality else None
        ds_dicts.append(ds_dict)

    return {
        'items': ds_dicts,
        'all_fields': all_fields + ['modality_name'],
        'selected_fields': selected_fields,
        'entity_type': 'drug_substance',
        'entity_plural': 'drug_substances',
        'table_id': 'drugSubstancesTable'
    }


def inline_update_drug_substance_field(ds_id: int, field: str, value):
    """Updates a single field on a drug substance."""
    ds = DrugSubstance.query.get(ds_id)
    if not ds:
        return None, "Drug Substance not found."

    if not hasattr(ds, field):
        return None, f"Field '{field}' does not exist."

    if field == 'code':
        if not value or not str(value).strip():
            return None, "Code cannot be empty."
        existing = DrugSubstance.query.filter(
            DrugSubstance.code == value,
            DrugSubstance.id != ds_id
        ).first()
        if existing:
            return None, f"Code '{value}' already exists."

    setattr(ds, field, value)
    db.session.commit()
    return ds, "Drug Substance updated."


def create_drug_substance(data: dict):
    """Creates a new drug substance."""
    # Resolve modality if provided by name
    if 'modality_name' in data:
        modality = Modality.query.filter_by(modality_name=data.pop('modality_name')).first()
        if modality:
            data['modality_id'] = modality.modality_id

    ds = DrugSubstance(**data)
    db.session.add(ds)
    db.session.commit()
    return ds


def delete_drug_substance(ds_id: int):
    """Deletes a drug substance by ID."""
    ds = DrugSubstance.query.get(ds_id)
    if not ds:
        return False, "Drug Substance not found."

    db.session.delete(ds)
    db.session.commit()
    return True, "Drug Substance deleted."


def get_drug_substances_by_modality(modality_id: int):
    """Get all drug substances for a specific modality."""
    return DrugSubstance.query.filter_by(modality_id=modality_id).order_by(DrugSubstance.code).all()


def get_drug_substances_by_status(status: str):
    """Get all drug substances with a specific status."""
    return DrugSubstance.query.filter_by(status=status).order_by(DrugSubstance.code).all()
