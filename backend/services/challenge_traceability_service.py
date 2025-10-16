# C:\Users\glutholi\CODE\PipelineIntelligence\backend\services\challenge_traceability_service.py

from ..models import Modality, ProcessTemplate, TemplateStage, ProcessStage, ManufacturingTechnology, ManufacturingChallenge
from ..db import db
from sqlalchemy.orm import joinedload
from collections import defaultdict

def get_full_process_hierarchy_for_template(template_id):
    """
    Gets all stages for a template and organizes them under their top-level phases,
    respecting the template's specified order.
    """
    template_stages_query = db.session.query(TemplateStage).filter(
        TemplateStage.template_id == template_id
    ).order_by(TemplateStage.stage_order).options(
        joinedload(TemplateStage.stage).joinedload(ProcessStage.parent)
    ).all()

    phases = {}
    for ts in template_stages_query:
        stage = ts.stage
        if not stage:
            continue

        current = stage
        while current.parent:
            current = current.parent
        
        phase_name = current.stage_name
        
        if phase_name not in phases:
            phases[phase_name] = {
                "phase_name": phase_name,
                "phase_id": current.stage_id,
                "stages": []
            }
        
        phases[phase_name]["stages"].append({
            "stage_obj": stage,
            "technologies": []
        })
        
    # --- START OF MODIFICATION ---
    phase_list = list(phases.values())
    
    # Define the desired order
    order_preference = {
        "Drug Substance Manufacturing": 0,
        "Drug Product Manufacturing": 1,
        # Add other phases here if their order matters, giving them higher numbers
    }
    
    # Sort the list of phases based on the preference
    phase_list.sort(key=lambda p: order_preference.get(p['phase_name'], 99))
    
    return phase_list
    # --- END OF MODIFICATION ---

def get_traceability_data(modality_id=None, template_id=None, challenge_id=None):
    """
    Fetches traceability data using the correct three-tier filtering logic:
    1. Template-specific technologies (template_id matches)
    2. Modality-specific technologies (ANY linked modality_id matches)
    3. Generic technologies (NO modality links)
    """
    if not modality_id or not template_id:
        return {"error": "Please select both a Modality and a Process Template."}

    # Step 1: Identify the Process Stages in Scope
    structured_process = get_full_process_hierarchy_for_template(template_id)
    stage_map = {
        stage_dict['stage_obj'].stage_id: stage_dict
        for phase in structured_process
        for stage_dict in phase['stages']
    }
    stage_ids_in_template = list(stage_map.keys())
    if not stage_ids_in_template:
        return structured_process

    # Step 2 & 3: Find and correctly filter technologies using three-tier logic
    # NEW: Use subquery to check junction table for modality membership
    from ..models import TechnologyModality
    from sqlalchemy.orm import joinedload

    technologies_query = db.session.query(ManufacturingTechnology).options(
        joinedload(ManufacturingTechnology.challenges)
    ).filter(
        # Condition 1: Must belong to one of the template's stages
        ManufacturingTechnology.stage_id.in_(stage_ids_in_template),

        # Condition 2: Must match one of three inheritance patterns
        db.or_(
            # Rule 1: Template-Specific Match
            ManufacturingTechnology.template_id == template_id,

            # Rule 2: Modality-Specific Match (check junction table)
            ManufacturingTechnology.technology_id.in_(
                db.session.query(TechnologyModality.technology_id)
                .filter(TechnologyModality.modality_id == modality_id)
            ),

            # Rule 3: Generic Match (NO modality links at all)
            ~db.session.query(TechnologyModality).filter(
                TechnologyModality.technology_id == ManufacturingTechnology.technology_id
            ).exists()
        )
    )

    technologies = technologies_query.all()

    # Populate the structure with the correctly filtered technologies
    for tech in technologies:
        if tech.stage_id in stage_map:
            tech_data = {
                "tech_obj": tech,
                "challenges": tech.challenges
            }
            stage_map[tech.stage_id]["technologies"].append(tech_data)

    # Step 4: Convert to JSON-serializable format for the frontend
    final_output = []
    for phase in structured_process:
        phase_data = {
            "phase_name": phase["phase_name"],
            "stages": []
        }
        for stage_dict in phase["stages"]:
            stage_data = {
                "stage_name": stage_dict["stage_obj"].stage_name,
                "stage_description": stage_dict["stage_obj"].short_description,
                "technologies": []
            }
            sorted_technologies = sorted(stage_dict["technologies"], key=lambda t: t['tech_obj'].technology_name)

            for tech_dict in sorted_technologies:
                sorted_challenges = sorted(tech_dict["challenges"], key=lambda c: c.challenge_name)

                tech_data = {
                    "tech_name": tech_dict["tech_obj"].technology_name,
                    "tech_short_description": tech_dict["tech_obj"].short_description,  # ADD THIS LINE
                    "complexity": tech_dict["tech_obj"].complexity_rating,
                    "challenges": [
                        {
                            "challenge_name": c.challenge_name,
                            "challenge_category": c.challenge_category,
                            "challenge_short_description": c.short_description,  # ADD THIS LINE
                            "severity_level": c.severity_level,  # Also useful for tooltips
                        } for c in sorted_challenges
                    ]
                }
                stage_data["technologies"].append(tech_data)
            phase_data["stages"].append(stage_data)
        final_output.append(phase_data)

    return final_output

def get_available_filters():
    """
    Returns all available modalities, templates, and challenges for filter dropdowns.
    """
    modalities = Modality.query.order_by(Modality.modality_name).all()
    templates = ProcessTemplate.query.order_by(ProcessTemplate.template_name).all()
    challenges = ManufacturingChallenge.query.order_by(ManufacturingChallenge.challenge_name).all()

    return {
        "modalities": [{"id": m.modality_id, "name": m.modality_name} for m in modalities],
        "templates": [{"id": t.template_id, "name": t.template_name} for t in templates],
        "challenges": [{"id": c.challenge_id, "name": c.challenge_name} for c in challenges]
    }

def get_templates_by_modality(modality_id):
    """
    Returns templates that belong to a specific modality.
    Used for cascade filtering in the UI.
    """
    if not modality_id:
        templates = ProcessTemplate.query.order_by(ProcessTemplate.template_name).all()
    else:
        templates = ProcessTemplate.query.filter_by(modality_id=modality_id)\
            .order_by(ProcessTemplate.template_name).all()
    
    return [{"id": t.template_id, "name": t.template_name, "modality_id": t.modality_id} 
            for t in templates]