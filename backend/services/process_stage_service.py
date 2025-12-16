# backend/services/process_stage_service.py
from flask import session
from sqlalchemy import inspect
from ..models import ProcessStage, db

DEFAULT_STAGE_COLUMNS = [
    'stage_name', 'stage_category', 'hierarchy_level',
    'short_description', 'parent_stage_id', 'stage_order'
]


def get_hierarchical_stages():
    """
    Returns process stages organized hierarchically for visualization.
    """
    all_stages = ProcessStage.query.order_by(
        ProcessStage.hierarchy_level,
        ProcessStage.stage_order
    ).all()

    stage_map = {stage.stage_id: stage for stage in all_stages}

    node_map = {
        stage.stage_id: {
            'stage': stage,
            'children': []
        }
        for stage in all_stages
    }

    root_nodes = []
    for stage in all_stages:
        node = node_map[stage.stage_id]
        if stage.parent_stage_id:
            parent_node = node_map.get(stage.parent_stage_id)
            if parent_node:
                parent_node['children'].append(node)
        else:
            root_nodes.append(node)

    return root_nodes


def get_process_stage_table_context(requested_columns=None):
    """
    Fetches all process stages and prepares context for rendering the process stages table.
    Returns a dict with: items, all_fields, selected_fields, entity_type, table_id, entity_plural.
    """
    stages = ProcessStage.query.order_by(
        ProcessStage.hierarchy_level,
        ProcessStage.stage_order
    ).all()

    all_fields = ProcessStage.get_all_fields()

    # Determine selected columns
    if requested_columns:
        selected_fields = [f for f in requested_columns.split(',') if f in all_fields]
    else:
        selected_fields = [f for f in DEFAULT_STAGE_COLUMNS if f in all_fields]

    return {
        'items': stages,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'process_stages',
        'table_id': 'process-stages-table',
        'entity_plural': 'process_stages'
    }


def inline_update_stage_field(stage_id, field_name, new_value):
    """
    Updates a single field on a ProcessStage. Returns (stage, message) tuple.
    """
    stage = ProcessStage.query.get(stage_id)
    if not stage:
        return None, "Process stage not found."

    all_fields = ProcessStage.get_all_fields()
    if field_name not in all_fields:
        return None, f"Field '{field_name}' is not editable or does not exist."

    # Handle special fields
    if field_name == 'parent_stage_id':
        # Validate parent exists and prevent circular references
        if new_value:
            try:
                parent_id = int(new_value)
                parent = ProcessStage.query.get(parent_id)
                if not parent:
                    return None, "Parent stage not found."
                if parent_id == stage_id:
                    return None, "A stage cannot be its own parent."
                # Check for circular references
                current = parent
                while current.parent_stage_id:
                    if current.parent_stage_id == stage_id:
                        return None, "Circular reference detected."
                    current = ProcessStage.query.get(current.parent_stage_id)
                setattr(stage, field_name, parent_id)
            except (ValueError, TypeError):
                return None, "Invalid parent stage ID."
        else:
            setattr(stage, field_name, None)
    elif field_name in ['hierarchy_level', 'stage_order']:
        try:
            setattr(stage, field_name, int(new_value) if new_value else None)
        except (ValueError, TypeError):
            return None, f"Invalid value for {field_name}."
    else:
        # String fields
        setattr(stage, field_name, new_value if new_value else None)

    db.session.commit()
    return stage, f"Updated {field_name} successfully."


def get_stage_details(stage_id):
    """
    Fetches a single process stage.
    """
    stage = ProcessStage.query.get(stage_id)
    if not stage:
        return None

    return {
        "stage": stage
    }
