# backend/routes/indication_routes.py
from flask import Blueprint, render_template, g
from flask_login import login_required
from ..services import indication_service

indication_routes = Blueprint('indications', __name__, url_prefix='/indications')

@indication_routes.route('/')
@login_required
def list_indications():
    indications = indication_service.get_all_indications(g.db_session)
    return render_template('indications.html', title="Indications", indications=indications)