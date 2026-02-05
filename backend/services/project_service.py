# backend/services/project_service.py
from sqlalchemy.orm import joinedload
from sqlalchemy import extract
from ..db import db
from ..models import Project, DrugSubstance, DrugProduct


def get_all_projects():
    """Retrieves all projects with relationships, ordered by name."""
    return Project.query.options(
        joinedload(Project.drug_substances),
        joinedload(Project.drug_products)
    ).order_by(Project.name).all()


def get_project_by_id(project_id: int):
    """Retrieves a single project by ID with all relationships."""
    return Project.query.options(
        joinedload(Project.drug_substances).joinedload(DrugSubstance.modality),
        joinedload(Project.drug_products)
    ).get(project_id)


def get_project_by_name(name: str):
    """Retrieves a single project by name."""
    return Project.query.filter_by(name=name).first()


def get_project_table_context(requested_columns_str: str = None):
    """Prepares the full context needed for rendering the dynamic projects table."""
    DEFAULT_COLUMNS = ['name', 'indication', 'project_type', 'administration', 'launch']
    EXTENDED_FIELDS = ['drug_substance_count', 'drug_product_count', 'drug_substance_codes', 'drug_product_codes']

    all_fields = Project.get_all_fields()
    valid_fields = all_fields + EXTENDED_FIELDS

    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in valid_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    projects = get_all_projects()

    # Convert SQLAlchemy objects to dictionaries for the template
    project_dicts = []
    for p in projects:
        p_dict = {field: getattr(p, field) for field in all_fields}
        # Format dates for display
        for date_field in ['sod', 'dsmm3', 'dsmm4', 'dpmm3', 'dpmm4', 'rofd', 'submission', 'launch']:
            if p_dict.get(date_field):
                p_dict[date_field] = p_dict[date_field].isoformat()
        # Add related counts and codes
        p_dict['drug_substance_count'] = len(p.drug_substances)
        p_dict['drug_product_count'] = len(p.drug_products)
        p_dict['drug_substance_codes'] = ', '.join([ds.code for ds in p.drug_substances]) or '-'
        p_dict['drug_product_codes'] = ', '.join([dp.code for dp in p.drug_products]) or '-'
        project_dicts.append(p_dict)

    return {
        'items': project_dicts,
        'all_fields': all_fields + EXTENDED_FIELDS,
        'selected_fields': selected_fields,
        'entity_type': 'project',
        'entity_plural': 'projects',
        'table_id': 'projectsTable'
    }


def inline_update_project_field(project_id: int, field: str, value):
    """Updates a single field on a project."""
    # These are computed display fields, not editable columns
    NON_EDITABLE_FIELDS = ['drug_substance_count', 'drug_product_count', 'drug_substance_codes', 'drug_product_codes']

    if field in NON_EDITABLE_FIELDS:
        return None, f"Field '{field}' is read-only. Edit relationships on the project detail page."

    project = Project.query.get(project_id)
    if not project:
        return None, "Project not found."

    if not hasattr(project, field):
        return None, f"Field '{field}' does not exist."

    if field == 'name':
        if not value or not str(value).strip():
            return None, "Name cannot be empty."
        existing = Project.query.filter(
            Project.name == value,
            Project.id != project_id
        ).first()
        if existing:
            return None, f"Project name '{value}' already exists."

    # Handle date fields
    if field in ['sod', 'dsmm3', 'dsmm4', 'dpmm3', 'dpmm4', 'rofd', 'submission', 'launch']:
        from datetime import datetime
        if value:
            try:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return None, f"Invalid date format for '{field}'. Use YYYY-MM-DD."
        else:
            value = None

    setattr(project, field, value)
    db.session.commit()
    return project, "Project updated."


def create_project(data: dict):
    """Creates a new project."""
    from datetime import datetime

    # Convert date strings to date objects
    date_fields = ['sod', 'dsmm3', 'dsmm4', 'dpmm3', 'dpmm4', 'rofd', 'submission', 'launch']
    for field in date_fields:
        if field in data and data[field]:
            if isinstance(data[field], str):
                data[field] = datetime.strptime(data[field], '%Y-%m-%d').date()

    project = Project(**data)
    db.session.add(project)
    db.session.commit()
    return project


def delete_project(project_id: int):
    """Deletes a project by ID."""
    project = Project.query.get(project_id)
    if not project:
        return False, "Project not found."

    db.session.delete(project)
    db.session.commit()
    return True, "Project deleted."


def get_projects_by_launch_year(year: int):
    """Get all projects launching in a specific year."""
    return Project.query.filter(
        extract('year', Project.launch) == year
    ).order_by(Project.launch).all()


def get_projects_by_indication(indication: str):
    """Get all projects for a specific indication."""
    return Project.query.filter_by(indication=indication).order_by(Project.name).all()


def get_projects_in_timeline_range(start_year: int, end_year: int):
    """Get all projects with launch dates in a given range."""
    from datetime import date
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    return Project.query.filter(
        Project.launch.between(start_date, end_date)
    ).order_by(Project.launch).all()


def link_drug_substance(project_id: int, ds_id: int):
    """Link a drug substance to a project."""
    project = Project.query.get(project_id)
    ds = DrugSubstance.query.get(ds_id)

    if not project or not ds:
        return False, "Project or Drug Substance not found."

    if ds not in project.drug_substances:
        project.drug_substances.append(ds)
        db.session.commit()
        return True, "Link created."
    return True, "Link already exists."


def unlink_drug_substance(project_id: int, ds_id: int):
    """Unlink a drug substance from a project."""
    project = Project.query.get(project_id)
    ds = DrugSubstance.query.get(ds_id)

    if not project or not ds:
        return False, "Project or Drug Substance not found."

    if ds in project.drug_substances:
        project.drug_substances.remove(ds)
        db.session.commit()
        return True, "Link removed."
    return True, "No link existed."


def link_drug_product(project_id: int, dp_id: int):
    """Link a drug product to a project."""
    project = Project.query.get(project_id)
    dp = DrugProduct.query.get(dp_id)

    if not project or not dp:
        return False, "Project or Drug Product not found."

    if dp not in project.drug_products:
        project.drug_products.append(dp)
        db.session.commit()
        return True, "Link created."
    return True, "Link already exists."


def unlink_drug_product(project_id: int, dp_id: int):
    """Unlink a drug product from a project."""
    project = Project.query.get(project_id)
    dp = DrugProduct.query.get(dp_id)

    if not project or not dp:
        return False, "Project or Drug Product not found."

    if dp in project.drug_products:
        project.drug_products.remove(dp)
        db.session.commit()
        return True, "Link removed."
    return True, "No link existed."


def get_timeline_overview(start_year: int = None, end_year: int = None):
    """
    Get timeline overview data for Gantt-chart visualization.
    Returns projects with all related DS/DP information.
    """
    query = Project.query.options(
        joinedload(Project.drug_substances),
        joinedload(Project.drug_products)
    )

    if start_year and end_year:
        from datetime import date
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        query = query.filter(Project.launch.between(start_date, end_date))

    projects = query.order_by(Project.launch).all()

    return [{
        'id': p.id,
        'name': p.name,
        'indication': p.indication,
        'timeline': p.get_timeline_dict(),
        'drug_substances': [{'code': ds.code, 'inn': ds.inn} for ds in p.drug_substances],
        'drug_products': [{'code': dp.code, 'pharm_form': dp.pharm_form} for dp in p.drug_products]
    } for p in projects]
