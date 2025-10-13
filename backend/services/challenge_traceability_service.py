# /backend/services/challenge_traceability_service.py

from ..models import Modality, ProcessTemplate, TemplateStage, ProcessStage, ManufacturingTechnology, ManufacturingChallenge
from ..db import db
from sqlalchemy.orm import joinedload

def get_traceability_data(modality_id=None, template_id=None, challenge_id=None):
    """
    Fetches traceability data for ONLY Stage → Technology → Challenge.
    Requires both modality_id and template_id to be set.
    
    Now uses the new modality_id and template_id fields on technologies
    for accurate filtering.
    """
    nodes = []
    links = []
    node_ids = set()
    
    # Validation: Both modality and template must be selected
    if not modality_id or not template_id:
        return {"nodes": [], "links": [], "error": "Please select both Modality and Template"}
    
    # Query the chain with proper technology filtering
    query = db.session.query(
        ProcessStage, ManufacturingTechnology, ManufacturingChallenge
    ).join(TemplateStage, ProcessStage.stage_id == TemplateStage.stage_id)\
     .join(ProcessTemplate, TemplateStage.template_id == ProcessTemplate.template_id)\
     .join(ManufacturingTechnology, ProcessStage.stage_id == ManufacturingTechnology.stage_id)\
     .join(ManufacturingChallenge, ManufacturingTechnology.technology_id == ManufacturingChallenge.technology_id)\
     .filter(ProcessTemplate.template_id == template_id)\
     .filter(ProcessTemplate.modality_id == modality_id)\
     .filter(
         db.or_(
             # Technology is template-specific and matches our template
             ManufacturingTechnology.template_id == template_id,
             # OR technology is modality-wide (applies to all templates in modality)
             db.and_(
                 ManufacturingTechnology.modality_id == modality_id,
                 ManufacturingTechnology.template_id.is_(None)
             ),
             # OR technology is legacy/stage-only (no modality/template specified)
             # Note: You may want to remove this clause after migration is complete
             db.and_(
                 ManufacturingTechnology.modality_id.is_(None),
                 ManufacturingTechnology.template_id.is_(None)
             )
         )
     )
    
    results = query.all()
    
    for stage, tech, chal in results:
        # Add Stage node (level 0)
        if f"stage_{stage.stage_id}" not in node_ids:
            nodes.append({
                "id": f"stage_{stage.stage_id}",
                "type": "stage",
                "name": stage.stage_name,
                "level": 0,
                "badge": stage.stage_category
            })
            node_ids.add(f"stage_{stage.stage_id}")
        
        # Add Technology node (level 1)
        if f"technology_{tech.technology_id}" not in node_ids:
            badge = f"Complexity: {tech.complexity_rating}/10" if tech.complexity_rating else None
            # Add scope indicator
            if tech.template_id:
                badge = f"{badge} • Template-Specific" if badge else "Template-Specific"
            elif tech.modality_id:
                badge = f"{badge} • Modality-Wide" if badge else "Modality-Wide"
            
            nodes.append({
                "id": f"technology_{tech.technology_id}",
                "type": "technology",
                "name": tech.technology_name,
                "level": 1,
                "badge": badge
            })
            node_ids.add(f"technology_{tech.technology_id}")
        
        # Add Challenge node (level 2)
        if f"challenge_{chal.challenge_id}" not in node_ids:
            nodes.append({
                "id": f"challenge_{chal.challenge_id}",
                "type": "challenge",
                "name": chal.challenge_name,
                "level": 2,
                "badge": chal.challenge_category
            })
            node_ids.add(f"challenge_{chal.challenge_id}")
        
        # Add links
        links.append({
            "source": f"stage_{stage.stage_id}",
            "target": f"technology_{tech.technology_id}",
            "pathway": "process_derived"
        })
        links.append({
            "source": f"technology_{tech.technology_id}",
            "target": f"challenge_{chal.challenge_id}",
            "pathway": "process_derived"
        })
    
    # Deduplicate links
    unique_links = [dict(t) for t in {tuple(d.items()) for d in links}]
    
    return {"nodes": nodes, "links": unique_links}

def get_pathway_a_data(modality_id=None):
    """
    Returns process-derived pathway:
    Modality → Templates → Stages → Technologies → Challenges
    """
    nodes = []
    links = []
    node_ids = set()

    query = db.session.query(
        Modality, ProcessTemplate, TemplateStage, ProcessStage, ManufacturingTechnology, ManufacturingChallenge
    ).join(ProcessTemplate, Modality.modality_id == ProcessTemplate.modality_id)\
     .join(TemplateStage, ProcessTemplate.template_id == TemplateStage.template_id)\
     .join(ProcessStage, TemplateStage.stage_id == ProcessStage.stage_id)\
     .join(ManufacturingTechnology, ProcessStage.stage_id == ManufacturingTechnology.stage_id)\
     .join(ManufacturingChallenge, ManufacturingTechnology.technology_id == ManufacturingChallenge.technology_id)

    if modality_id:
        query = query.filter(Modality.modality_id == modality_id)

    results = query.all()

    for mod, tmpl, t_stage, stage, tech, chal in results:
        # Add nodes if they don't exist
        if f"modality_{mod.modality_id}" not in node_ids:
            nodes.append({"id": f"modality_{mod.modality_id}", "type": "modality", "name": mod.modality_name, "level": 0})
            node_ids.add(f"modality_{mod.modality_id}")
        if f"template_{tmpl.template_id}" not in node_ids:
            nodes.append({"id": f"template_{tmpl.template_id}", "type": "template", "name": tmpl.template_name, "level": 1})
            node_ids.add(f"template_{tmpl.template_id}")
        if f"stage_{stage.stage_id}" not in node_ids:
            nodes.append({"id": f"stage_{stage.stage_id}", "type": "stage", "name": stage.stage_name, "level": 2})
            node_ids.add(f"stage_{stage.stage_id}")
        if f"technology_{tech.technology_id}" not in node_ids:
            nodes.append({"id": f"technology_{tech.technology_id}", "type": "technology", "name": tech.technology_name, "level": 3})
            node_ids.add(f"technology_{tech.technology_id}")
        if f"challenge_{chal.challenge_id}" not in node_ids:
            nodes.append({"id": f"challenge_{chal.challenge_id}", "type": "challenge", "name": chal.challenge_name, "level": 4})
            node_ids.add(f"challenge_{chal.challenge_id}")

        # Add links
        links.append({"source": f"modality_{mod.modality_id}", "target": f"template_{tmpl.template_id}", "pathway": "process_derived"})
        links.append({"source": f"template_{tmpl.template_id}", "target": f"stage_{stage.stage_id}", "pathway": "process_derived"})
        links.append({"source": f"stage_{stage.stage_id}", "target": f"technology_{tech.technology_id}", "pathway": "process_derived"})
        links.append({"source": f"technology_{tech.technology_id}", "target": f"challenge_{chal.challenge_id}", "pathway": "process_derived"})
    
    # Deduplicate links
    unique_links = [dict(t) for t in {tuple(d.items()) for d in links}]
    return {"nodes": nodes, "links": unique_links}


def get_pathway_b_data(modality_id=None):
    """
    Returns direct pathway: Modality → Challenges (direct links)
    This uses your `modality_challenges` association table.
    """
    nodes = []
    links = []
    node_ids = set()

    query = db.session.query(Modality, ManufacturingChallenge)\
        .join(Modality.modality_challenges)\
        .join(ManufacturingChallenge)

    if modality_id:
        query = query.filter(Modality.modality_id == modality_id)
    
    results = query.all()

    for mod, chal in results:
        if f"modality_{mod.modality_id}" not in node_ids:
            nodes.append({"id": f"modality_{mod.modality_id}", "type": "modality", "name": mod.modality_name, "level": 0})
            node_ids.add(f"modality_{mod.modality_id}")
        if f"challenge_{chal.challenge_id}" not in node_ids:
            nodes.append({"id": f"challenge_{chal.challenge_id}", "type": "challenge", "name": chal.challenge_name, "level": 4})
            node_ids.add(f"challenge_{chal.challenge_id}")
        
        links.append({"source": f"modality_{mod.modality_id}", "target": f"challenge_{chal.challenge_id}", "pathway": "direct"})

    return {"nodes": nodes, "links": links}

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