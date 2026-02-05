# Update backend/routes/analytics_routes.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..services.pipeline_timeline_service import get_timeline_service
from ..services.strategic_analytics_service import get_weighted_challenges_data, get_challenge_modality_matrix

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
        "dateSource": "launch",
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


@analytics_routes.route('/weighted-challenges')
@login_required
def weighted_challenges():
    """
    Zeigt eine priorisierte Liste von Manufacturing Challenges.
    """
    challenges = get_weighted_challenges_data()

    return render_template(
        'analytics/weighted_challenges.html',
        title="Challenge Prioritization Matrix",
        challenges=challenges
    )


@analytics_routes.route('/api/weighted-challenges', methods=['GET'])
@login_required
def get_weighted_challenges():
    """
    API endpoint to fetch weighted manufacturing challenges data.

    Returns a list of challenges ranked by:
    - Frequency (number of affected products)
    - Urgency (next launch year)
    - Process area (Drug Substance vs. Drug Product)
    """
    try:
        data = get_weighted_challenges_data()
        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_routes.route('/challenge-matrix')
@login_required
def challenge_matrix():
    """
    Interactive matrix view: Challenges (rows) x Modalities (columns).
    Filterable by value step, with selectable display values (applicable/impact/maturity).
    """
    data = get_challenge_modality_matrix()
    return render_template(
        'analytics/challenge_matrix.html',
        title="Need Matrix V0.1",
        **data
    )


@analytics_routes.route('/api/challenge-matrix', methods=['GET'])
@login_required
def get_challenge_matrix_data():
    """
    API endpoint for challenge-modality matrix data.
    """
    try:
        data = get_challenge_modality_matrix()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500