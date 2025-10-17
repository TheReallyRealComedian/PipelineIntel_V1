# Update backend/routes/analytics_routes.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services.pipeline_timeline_service import get_timeline_service

analytics_routes = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_routes.route('/pipeline-timeline')
@login_required
def pipeline_timeline():
    """
    Interactive pipeline visualization with configurable timelines and groupings.
    """
    return render_template('analytics/pipeline_timeline.html', 
                           title="Pipeline Timeline")

@analytics_routes.route('/api/pipeline-timeline-data', methods=['POST'])
@login_required
def get_pipeline_timeline_data():
    """
    API endpoint to fetch timeline data based on configuration.
    
    Expects JSON body with configuration:
    {
        "timelineMode": "year",
        "groupingMode": "modality",
        "elementType": "product",
        ...
    }
    
    Returns structured timeline data.
    """
    try:
        config = request.get_json()
        
        if not config:
            return jsonify({'error': 'No configuration provided'}), 400
        
        # Get timeline service and fetch data
        service = get_timeline_service()
        data = service.get_timeline_data(config)
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_routes.route('/capability-gaps')
@login_required
def capability_gaps():
    # Placeholder for the gap analysis dashboard
    return render_template('analytics/placeholder.html', 
                           title="Capability Gap Analysis",
                           message="This dashboard will show the gaps between required capabilities for our pipeline and the currently available capabilities in our manufacturing network.")