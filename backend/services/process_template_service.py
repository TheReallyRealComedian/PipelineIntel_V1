# backend/services/process_template_service.py
from ..models import ProcessTemplate, TemplateStage, ProcessStage, Modality
from ..db import db

def get_process_template_table_context(requested_columns=None):
    """
    Get all process templates with their related data for table display.
    """
    # Define all available fields for process templates
    all_fields = [
        'template_id', 'template_name', 'description', 'modality_name', 
        'created_at', 'stage_count'
    ]
    
    # Default columns to show
    default_fields = ['template_name', 'modality_name', 'stage_count', 'created_at']
    
    # Determine which columns to show
    if requested_columns:
        selected_fields = [f for f in requested_columns.split(',') if f in all_fields]
    else:
        selected_fields = default_fields
    
    # Query templates with modality information
    templates_query = db.session.query(
        ProcessTemplate,
        Modality.modality_name.label('modality_name')
    ).outerjoin(Modality, ProcessTemplate.modality_id == Modality.modality_id)
    
    # Transform to dictionaries with computed fields
    items = []
    for template, modality_name in templates_query.all():
        item_dict = {
            'template_id': template.template_id,
            'template_name': template.template_name,
            'description': template.description,
            'modality_name': modality_name,
            'created_at': template.created_at,
            'stage_count': len(template.stages)
        }
        items.append(item_dict)
    
    return {
        'items': items,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'process_template',
        'entity_plural': 'process_templates',
        'table_id': 'process-templates-table'
    }

def get_template_with_stages(template_id):
    """
    Get a process template with its associated stages for detailed view.
    """
    template = ProcessTemplate.query.get(template_id)
    if not template:
        return None
    
    # Get template stages ordered by stage_order
    template_stages = db.session.query(
        TemplateStage, ProcessStage
    ).join(
        ProcessStage, TemplateStage.stage_id == ProcessStage.stage_id
    ).filter(
        TemplateStage.template_id == template_id
    ).order_by(TemplateStage.stage_order).all()
    
    stages_data = []
    for template_stage, process_stage in template_stages:
        stages_data.append({
            'template_stage': template_stage,
            'process_stage': process_stage,
            'stage_name': process_stage.stage_name,
            'stage_category': process_stage.stage_category,
            'hierarchy_level': process_stage.hierarchy_level,
            'stage_order': template_stage.stage_order,
            'is_required': template_stage.is_required,
            'base_capabilities': template_stage.base_capabilities
        })
    
    return {
        'template': template,
        'stages': stages_data,
        'modality': template.modality
    }

def inline_update_template_field(template_id, field_name, new_value):
    """
    Update a single field of a process template.
    """
    template = ProcessTemplate.query.get(template_id)
    if not template:
        return None, "Process template not found."
    
    try:
        if field_name == 'template_name':
            if not new_value or new_value.strip() == '':
                return None, "Template name cannot be empty."
            
            # Check for duplicates
            existing = ProcessTemplate.query.filter(
                ProcessTemplate.template_name == new_value.strip(),
                ProcessTemplate.template_id != template_id
            ).first()
            if existing:
                return None, f"Template name '{new_value.strip()}' already exists."
                
            template.template_name = new_value.strip()
            
        elif field_name == 'description':
            template.description = new_value.strip() if new_value else None
            
        elif field_name == 'modality_name':
            if new_value and new_value.strip():
                modality = Modality.query.filter_by(modality_name=new_value.strip()).first()
                if not modality:
                    return None, f"Modality '{new_value.strip()}' not found."
                template.modality_id = modality.modality_id
            else:
                template.modality_id = None
                
        else:
            return None, f"Field '{field_name}' cannot be updated."
        
        db.session.commit()
        return template, f"Updated {field_name} successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Update failed: {str(e)}"

def delete_process_template(template_id):
    """
    Delete a process template and all its associated template stages.
    """
    template = ProcessTemplate.query.get(template_id)
    if not template:
        return False, "Process template not found."
    
    try:
        # Delete associated template stages (cascade should handle this, but being explicit)
        TemplateStage.query.filter_by(template_id=template_id).delete()
        
        # Delete the template
        db.session.delete(template)
        db.session.commit()
        
        return True, f"Process template '{template.template_name}' deleted successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to delete template: {str(e)}"

def get_all_templates_summary():
    """
    Get a summary of all templates for analytics/overview purposes.
    """
    templates = db.session.query(
        ProcessTemplate.template_name,
        ProcessTemplate.description,
        Modality.modality_name.label('modality_name'),
        db.func.count(TemplateStage.stage_id).label('stage_count')
    ).outerjoin(
        Modality, ProcessTemplate.modality_id == Modality.modality_id
    ).outerjoin(
        TemplateStage, ProcessTemplate.template_id == TemplateStage.template_id
    ).group_by(
        ProcessTemplate.template_id, 
        ProcessTemplate.template_name, 
        ProcessTemplate.description,
        Modality.modality_name
    ).all()
    
    return [
        {
            'template_name': t.template_name,
            'modality_name': t.modality_name,
            'stage_count': t.stage_count,
            'description': t.description
        }
        for t in templates
    ]