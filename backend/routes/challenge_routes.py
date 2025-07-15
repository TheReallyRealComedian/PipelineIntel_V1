# backend/routes/challenge_routes.py
from flask import Blueprint, render_template, g
from flask_login import login_required
from ..services import challenge_service

challenge_routes = Blueprint('challenges', __name__, url_prefix='/challenges')

@challenge_routes.route('/')
@login_required
def list_challenges():
    challenges = challenge_service.get_all_challenges(g.db_session)
    return render_template('manufacturing_challenges.html', title="Manufacturing Challenges", challenges=challenges)