# backend/services/modality_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Modality, Product, ManufacturingCapability
from ..models import all_product_requirements_view # We will create this model for the view

def get_all_modalities(db_session: Session):
    """Retrieves all modalities, ordered by name."""
    return db_session.query(Modality).order_by(Modality.modality_name).all()

def get_modality_table_context(db_session: Session, requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic modalities table."""
    # UPDATED: Use 'short_description' instead of 'description' for the default view
    DEFAULT_COLUMNS = ['modality_name', 'modality_category', 'short_description']
    
    all_fields = Modality.get_all_fields()
    
    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    modalities = get_all_modalities(db_session)
    
    # Convert SQLAlchemy objects to dictionaries for the template
    modality_dicts = [{field: getattr(m, field) for field in all_fields} for m in modalities]

    return {
        'items': modality_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'modality',
        'entity_plural': 'modalities', # ADD THIS LINE
        'table_id': 'modalitiesTable'
    }

# ADD THIS NEW FUNCTION FOR INLINE EDITING
def inline_update_modality_field(db_session: Session, modality_id: int, field: str, value: any):
    """Updates a single field on a modality."""
    modality = db_session.query(Modality).get(modality_id)
    if not modality:
        return None, "Modality not found."

    if not hasattr(modality, field):
        return None, f"Field '{field}' does not exist."
    
    if field == 'modality_name':
        if not value or not str(value).strip():
            return None, "Modality Name cannot be empty."
        existing = db_session.query(Modality).filter(
            Modality.modality_name == value, 
            Modality.modality_id != modality_id
        ).first()
        if existing:
            return None, f"Modality Name '{value}' already exists."

    setattr(modality, field, value)
    db_session.commit()
    return modality, "Modality updated."

def get_modality_complexity_analysis(db_session: Session, timeline_start: int, timeline_end: int):
    """
    Strategic query: Gathers complexity scores for modalities based on products launching within a given timeline.
    
    This function will be fully implemented later. For now, it serves as a placeholder.
    It would typically query the 'product_complexity_summary' view.
    """
    # Placeholder implementation
    print(f"Executing strategic query: Modality complexity for products launching between {timeline_start} and {timeline_end}.")
    # Example of what the query might look like:
    # results = db_session.query(
    #     Modality.modality_name,
    #     func.avg(product_complexity_summary.c.complexity_score).label('average_complexity'),
    #     func.count(Product.product_id).label('product_count')
    # ).join(Product, Modality.modality_id == Product.modality_id)\
    #  .join(product_complexity_summary, Product.product_id == product_complexity_summary.c.product_id)\
    #  .filter(Product.expected_launch_year.between(timeline_start, timeline_end))\
    #  .group_by(Modality.modality_name)\
    #  .order_by(func.avg(product_complexity_summary.c.complexity_score).desc())\
    #  .all()
    return []