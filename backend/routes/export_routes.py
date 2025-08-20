# backend/routes/export_routes.py
from flask import Blueprint, render_template, request, g
from flask_login import login_required
from ..services import export_service, product_service, indication_service, challenge_service, technology_service


export_bp = Blueprint('export', __name__, url_prefix='/export')

# Define the fields that users can select for each entity
SELECTABLE_FIELDS = {
    'products': [f.key for f in product_service.Product.__mapper__.attrs if not f.key.startswith('_')],
    'indications': [f.key for f in indication_service.Indication.__mapper__.attrs if not f.key.startswith('_')],
    'challenges': [f.key for f in challenge_service.ManufacturingChallenge.__mapper__.attrs if not f.key.startswith('_')],
    'technologies': [f.key for f in technology_service.ManufacturingTechnology.__mapper__.attrs if not f.key.startswith('_')]
}

@export_bp.route('/data-export', methods=['GET', 'POST'])
@login_required
def data_export_page():
    # Data to pass to the template
    context = {
        'title': "Custom Data Export",
        'prepared_json': "{}",
        'total_tokens': 0,
        'form_data': request.form if request.method == 'POST' else {}
    }

    # Fetch all items for the selection boxes
    all_items = {
        'products': product_service.get_all_products(g.db_session),
        'indications': indication_service.get_all_indications(g.db_session),
        'challenges': challenge_service.get_all_challenges(g.db_session),
        'technologies': technology_service.get_all_technologies(g.db_session),
    }
    context.update(all_items)
    context['selectable_fields'] = SELECTABLE_FIELDS

    if request.method == 'POST':
        # If form is submitted, process it and update the context
        prepared_json, total_tokens = export_service.prepare_json_export(g.db_session, request.form)
        context['prepared_json'] = prepared_json
        context['total_tokens'] = total_tokens

    return render_template('data_export.html', **context)