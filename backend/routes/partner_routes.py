# backend/routes/partner_routes.py
from flask import Blueprint, render_template, g
from flask_login import login_required
from ..services import partner_service

partner_routes = Blueprint('partners', __name__, url_prefix='/partners')

@partner_routes.route('/')
@login_required
def list_partners():
    partners = partner_service.get_all_partners(g.db_session)
    return render_template('partners.html', title="Partners", partners=partners)