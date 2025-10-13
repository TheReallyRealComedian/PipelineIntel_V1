# /backend/services/challenge_traceability_service.py

from ..models import Modality, ProcessTemplate, TemplateStage, ProcessStage, ManufacturingTechnology, ManufacturingChallenge
from ..db import db
from sqlalchemy.orm import joinedload, contains_eager
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

    # This dictionary will be ordered by stage_order from the template
    phases = {}
    
    for ts in template_stages_query:
        stage = ts.stage
        if not stage:
            continue

        # Find the top-level parent (the Phase)
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
        
        # Add the actual stage from the template to this phase
        phases[phase_name]["stages"].append({
            "stage_obj": stage,
            "technologies": []
        })
        
    return list(phases.values())


def get_traceability_data(modality_id=None, template_id=None, challenge_id=None):
    """
    Fetches traceability data as a hierarchical structure: Phase -> Stage -> Technology -> Challenge.
    Requires both modality_id and template_id.
    """
    if not modality_id or not template_id:
        return {"error": "Please select both a Modality and a Process Template."}

    # 1. Get the ordered hierarchical structure for the template
    structured_process = get_full_process_hierarchy_for_template(template_id)
    
    # Create a quick lookup map: stage_id -> stage_dict
    stage_map = {}
    for phase in structured_process:
        for stage_dict in phase['stages']:
            stage_map[stage_dict['stage_obj'].stage_id] = stage_dict

    # 2. Get all technologies and challenges linked to the stages in this template
    query = db.session.query(ManufacturingTechnology, ManufacturingChallenge)\
        .join(ManufacturingChallenge, ManufacturingTechnology.technology_id == ManufacturingChallenge.technology_id)\
        .filter(ManufacturingTechnology.stage_id.in_(stage_map.keys()))\
        .options(contains_eager(ManufacturingTechnology.challenges))

    results = query.all()

    # 3. Populate the structure with technologies and challenges
    tech_map = {}
    for tech, chal in results:
        if tech.technology_id not in tech_map:
            tech_map[tech.technology_id] = {
                "tech_obj": tech,
                "challenges": []
            }
            # Add this technology to the correct stage
            if tech.stage_id in stage_map:
                stage_map[tech.stage_id]["technologies"].append(tech_map[tech.technology_id])
        
        tech_map[tech.technology_id]["challenges"].append(chal)

    # 4. Convert SQLAlchemy objects to JSON-serializable dictionaries for the frontend
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
            for tech_dict in stage_dict["technologies"]:
                tech_data = {
                    "tech_name": tech_dict["tech_obj"].technology_name,
                    "complexity": tech_dict["tech_obj"].complexity_rating,
                    "challenges": [
                        {
                            "challenge_name": c.challenge_name,
                            "challenge_category": c.challenge_category,
                        } for c in tech_dict["challenges"]
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