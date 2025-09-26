# backend/services/process_stage_service.py
from flask import session
from sqlalchemy import inspect
from ..models import ProcessStage, db, ManufacturingChallenge
from sqlalchemy.orm import joinedload

DEFAULT_STAGE_COLUMNS = [
    'stage_name', 'stage_category', 'hierarchy_level',
    'short_description', 'parent_stage_id', 'stage_order'
]


def get_hierarchical_stages_with_challenges():
    """
    Returns process stages organized hierarchically, with associated challenges
    eager-loaded for high performance.
    """
    # 1. Fetch all stages in one query, and tell SQLAlchemy to also fetch all
    #    related challenges in a second, efficient query.
    all_stages = ProcessStage.query.options(
        joinedload(ProcessStage.challenges)
    ).order_by(ProcessStage.hierarchy_level, ProcessStage.stage_order).all()

    # 2. Build the tree structure in memory (much faster than repeated DB calls)
    stage_map = {stage.stage_id: stage for stage in all_stages}
    
    # Create a node structure that includes the stage and its children
    node_map = {
        stage.stage_id: {
            'stage': stage, 
            'challenges': sorted(stage.challenges, key=lambda c: c.challenge_name),
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


def get_hierarchical_stages():
    """
    Returns process stages organized hierarchically for visualization.
    """
    top_level = ProcessStage.get_top_level_phases()

    def build_tree(stage):
        return {
            'stage': stage,
            'children': [build_tree(child) for child in stage.children]
        }

    return [build_tree(stage) for stage in top_level]


def get_stage_details(stage_id):
    """
    Fetches a single process stage and its directly associated challenges.
    """
    stage = ProcessStage.query.get(stage_id)
    if not stage:
        return None

    # The 'challenges' backref from the model makes this easy
    associated_challenges = stage.challenges

    return {
        "stage": stage,
        "challenges": sorted(associated_challenges, key=lambda c: c.challenge_name)
    }


def update_stage_challenges(stage_id, challenge_ids):
    """
    Updates the list of challenges associated with a specific process stage.
    This is a full replacement operation.
    """
    stage = ProcessStage.query.get(stage_id)
    if not stage:
        return False, "Process stage not found."

    try:
        # Fetch the challenge objects that should be linked
        challenges_to_link = ManufacturingChallenge.query.filter(
            ManufacturingChallenge.challenge_id.in_(challenge_ids)
        ).all()

        # SQLAlchemy's relationship management handles the adds/removes automatically
        stage.challenges = challenges_to_link

        db.session.commit()
        return True, "Challenge associations updated successfully."
    except Exception as e:
        db.session.rollback()
        return False, f"An error occurred: {str(e)}"