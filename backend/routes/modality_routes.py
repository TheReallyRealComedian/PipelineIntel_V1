# backend/routes/modality_routes.py
from flask import Blueprint, render_template, g
from flask_login import login_required
from ..services import modality_service

modality_routes = Blueprint('modalities', __name__, url_prefix='/modalities')

@modality_routes.route('/')
@login_required
def list_modalities():
    modalities = modality_service.get_all_modalities(g.db_session)
    return render_template('modalities.html', title="Modalities", modalities=modalities)

@modality_routes.route('/complexity-analysis')
@login_required
def modality_complexity_analysis():
    # This is a placeholder for a future strategic analytics page
    # It will use modality_service.get_modality_complexity_analysis()
    return render_template('analytics/placeholder.html', 
                           title="Modality Complexity Analysis",
                           message="This page will contain a detailed analysis of manufacturing complexity driven by different modalities.")