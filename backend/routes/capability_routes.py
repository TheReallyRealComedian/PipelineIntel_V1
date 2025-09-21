# backend/routes/capability_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from ..services import capability_service

capability_routes = Blueprint(
    'capabilities',
    __name__,
    url_prefix='/capabilities'
)


@capability_routes.route('/')
@login_required
def list_capabilities():
    """Main page showing all manufacturing capabilities in a table."""
    requested_columns = request.args.get('columns')
    context = capability_service.get_capability_table_context(requested_columns)
    return render_template('capabilities.html', title="Manufacturing Capabilities", **context)


@capability_routes.route('/api/capabilities/<int:capability_id>/inline-update', methods=['PUT'])
@login_required
def inline_update_capability(capability_id):
    """API endpoint for inline editing of capability fields."""
    data = request.json
    if not data or len(data) != 1:
        return jsonify(success=False, message="Invalid update data."), 400

    field, value = list(data.items())[0]

    capability, message = capability_service.inline_update_capability_field(
        capability_id, field, value
    )

    if not capability:
        return jsonify(success=False, message=message), 400

    return jsonify(success=True, message=message)


@capability_routes.route('/matrix')
@login_required
def capability_matrix():
    """Matrix view showing capabilities across categories."""
    capabilities = capability_service.get_all_capabilities()
    
    # Group by category for better visualization
    by_category = {}
    for cap in capabilities:
        category = cap.capability_category or "Uncategorized"
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(cap)
    
    return render_template(
        'capabilities_matrix.html',
        title="Capability Matrix",
        capabilities_by_category=by_category
    )


@capability_routes.route('/complexity-analysis')
@login_required
def complexity_analysis():
    """Placeholder for capability complexity analysis."""
    return render_template(
        'analytics/placeholder.html',
        title="Capability Complexity Analysis",
        message="This page will show analysis of manufacturing capabilities by complexity weight, category, and approach."
    )