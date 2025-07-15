# backend/routes/settings_routes.py
from flask import Blueprint, g, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..services import settings_service

settings_routes = Blueprint('settings', __name__, url_prefix='/settings')

@settings_routes.route('/', methods=['GET', 'POST'])
@login_required
def manage_settings():
    try:
        # This logic remains the same
        user_settings = settings_service.get_user_llm_settings(g.db_session, current_user.id)
            
        if request.method == 'POST':
            success, message = settings_service.save_user_llm_settings(g.db_session, current_user, request.form)
            flash(message, "success" if success else "danger")
            return redirect(url_for('settings.manage_settings'))

        # The unnecessary data fetching for breadcrumbs is removed
        return render_template(
            'settings.html',
            title='Application Settings',
            settings=user_settings
        )
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")
        # Redirect to a safe page like the product list
        return redirect(url_for('products.list_products'))