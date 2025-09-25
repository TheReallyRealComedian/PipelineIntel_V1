# backend/routes/export_routes.py
from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from ..services import export_service
import datetime


export_bp = Blueprint('export', __name__, url_prefix='/export')

@export_bp.route('/data-export', methods=['GET', 'POST'])
@login_required
def data_export_page():
    # The service layer now prepares all the data needed for the page
    page_context = export_service.get_export_page_context()
    
    context = {
        'title': "Custom Data Export",
        'prepared_json': "{}",
        'total_tokens': 0,
        'form_data': request.form if request.method == 'POST' else {},
        **page_context  # Unpack the dictionaries from the service into the main context
    }

    if request.method == 'POST':
        prepared_json, total_tokens = export_service.prepare_json_export(request.form)
        context['prepared_json'] = prepared_json
        context['total_tokens'] = total_tokens

    return render_template('data_export.html', **context)

@export_bp.route('/full-database-export')
@login_required
def full_database_export():
    """Exports the entire database as a single JSON file."""
    json_data = export_service.export_full_database()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pipeline_intelligence_backup_{timestamp}.json"
    
    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )