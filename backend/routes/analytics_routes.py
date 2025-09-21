# backend/routes/analytics_routes.py
from flask import Blueprint, render_template
from flask_login import login_required

analytics_routes = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_routes.route('/manufacturing-forecast')
@login_required
def manufacturing_forecast():
    # Placeholder for the strategic dashboard
    return render_template('analytics/placeholder.html', 
                           title="Manufacturing Forecast",
                           message="This dashboard will provide a strategic forecast of manufacturing challenges, capability needs, and capacity constraints based on the product pipeline.")

@analytics_routes.route('/capability-gaps')
@login_required
def capability_gaps():
    # Placeholder for the gap analysis dashboard
    return render_template('analytics/placeholder.html', 
                           title="Capability Gap Analysis",
                           message="This dashboard will show the gaps between required capabilities for our pipeline and the currently available capabilities in our manufacturing network.")