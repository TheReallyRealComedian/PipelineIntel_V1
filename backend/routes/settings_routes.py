# backend/routes/settings_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..services import settings_service

settings_routes = Blueprint('settings', __name__, url_prefix='/settings')

@settings_routes.route('/', methods=['GET', 'POST'])
@login_required
def manage_settings():
    try:
        user_settings = settings_service.get_user_llm_settings(current_user.id)

        if request.method == 'POST':
            success, message = settings_service.save_user_llm_settings(current_user, request.form)
            flash(message, "success" if success else "danger")
            return redirect(url_for('settings.manage_settings'))

        return render_template(
            'settings.html',
            title='Application Settings',
            settings=user_settings
        )
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")
        return redirect(url_for('products.list_products'))