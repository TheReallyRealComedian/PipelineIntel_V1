# backend/routes/settings_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..services import settings_service, schema_service

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
    

@settings_routes.route('/database-schema')
@login_required
def database_schema():
    """Display the database schema diagram."""
    try:
        # Generate the diagram
        diagram_data, mime_type = schema_service.generate_schema_diagram(format='png')
        
        # Get statistics
        stats = schema_service.get_schema_statistics()
        
        return render_template(
            'database_schema.html',
            title='Database Schema',
            diagram_data=diagram_data,
            mime_type=mime_type,
            stats=stats
        )
    except Exception as e:
        flash(f"Error loading schema: {e}", "danger")
        return redirect(url_for('settings.manage_settings'))

@settings_routes.route('/database-schema/download/<format>')
@login_required
def download_schema(format):
    """Download schema diagram in specified format."""
    from flask import send_file
    import tempfile
    from eralchemy2 import render_er
    from ..db import db
    
    try:
        if format not in ['png', 'pdf', 'svg']:
            return jsonify({'error': 'Invalid format'}), 400
        
        # Generate diagram
        with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as tmp:
            tmp_path = tmp.name
        
        render_er(db.metadata, tmp_path)
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=f'database_schema.{format}',
            mimetype=f'image/{format}' if format != 'pdf' else 'application/pdf'
        )
        
    except Exception as e:
        flash(f"Error generating download: {e}", "danger")
        return redirect(url_for('settings.database_schema'))