# /backend/services/challenge_traceability_service.py

from ..models import Modality, ProcessTemplate, TemplateStage, ProcessStage, ManufacturingTechnology, ManufacturingChallenge
from ..db import db
from sqlalchemy.orm import joinedload

def get_traceability_data(modality_id=None, template_id=None, challenge_id=None):
    """
    Fetches the complete traceability chain.
    This is a complex query that combines both pathways.
    For simplicity, we'll build the node and link lists by calling the pathway-specific functions.
    """
    nodes = []
    links = []
    node_ids = set()

    # Fetch Pathway A data
    pathway_a_result = get_pathway_a_data(modality_id)
    for node in pathway_a_result['nodes']:
        if node['id'] not in node_ids:
            nodes.append(node)
            node_ids.add(node['id'])
    links.extend(pathway_a_result['links'])

    # Fetch Pathway B data
    pathway_b_result = get_pathway_b_data(modality_id)
    for node in pathway_b_result['nodes']:
        if node['id'] not in node_ids:
            nodes.append(node)
            node_ids.add(node['id'])
    links.extend(pathway_b_result['links'])
    
    # Note: Filtering by template_id and challenge_id would require more complex logic
    # to trace the graph and only include relevant nodes/links.
    # This implementation focuses on the primary modality_id filter.

    return {"nodes": nodes, "links": links}

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