# backend/routes/facility_routes.py
from flask import Blueprint, render_template, g
from flask_login import login_required
# We will create this service in a future step, for now, we query the model directly
from ..models import ManufacturingEntity

facility_routes = Blueprint('facilities', __name__, url_prefix='/facilities')

@facility_routes.route('/')
@login_required
def list_facilities():
    # For now, we fetch all entities. This can be refined later.
    facilities = g.db_session.query(ManufacturingEntity).order_by(ManufacturingEntity.entity_type, ManufacturingEntity.entity_name).all()
    return render_template('facilities.html', title="Manufacturing Facilities & Partners", facilities=facilities)