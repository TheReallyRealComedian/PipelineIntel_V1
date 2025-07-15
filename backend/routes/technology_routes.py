# backend/routes/technology_routes.py
from flask import Blueprint, render_template, g
from flask_login import login_required
from ..services import technology_service

technology_routes = Blueprint('technologies', __name__, url_prefix='/technologies')

@technology_routes.route('/')
@login_required
def list_technologies():
    technologies = technology_service.get_all_technologies(g.db_session)
    return render_template('manufacturing_technologies.html', title="Manufacturing Technologies", technologies=technologies)