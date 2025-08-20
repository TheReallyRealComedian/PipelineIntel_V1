# backend/routes/export_routes.py
from flask import Blueprint, render_template, request, g
from flask_login import login_required
from ..services import export_service


export_bp = Blueprint('export', __name__, url_prefix='/export')

@export_bp.route('/data-export', methods=['GET', 'POST'])
@login_required
def data_export_page():
    # The service layer now prepares all the data needed for the page
    page_context = export_service.get_export_page_context(g.db_session)
    
    context = {
        'title': "Custom Data Export",
        'prepared_json': "{}",
        'total_tokens': 0,
        'form_data': request.form if request.method == 'POST' else {},
        **page_context  # Unpack the dictionaries from the service into the main context
    }

    if request.method == 'POST':
        prepared_json, total_tokens = export_service.prepare_json_export(g.db_session, request.form)
        context['prepared_json'] = prepared_json
        context['total_tokens'] = total_tokens

    return render_template('data_export.html', **context)