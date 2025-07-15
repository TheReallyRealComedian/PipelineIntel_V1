# backend/routes/export_routes.py
from flask import Blueprint, Response, flash, redirect, url_for, g
from flask_login import login_required
# CORRECTED IMPORT PATH
from ..services import export_service
from ..models import Area
import datetime

export_routes = Blueprint('export', __name__, url_prefix='/export')

@export_routes.route('/database/json')
@login_required
def export_db_json():
    # This function call remains the same
    json_string = export_service.export_database_to_json_string()
    if json_string:
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"asset_tracker_db_export_{timestamp}.json"
        return Response(
            json_string,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    else:
        flash("Failed to export database.", "danger")
        return redirect(url_for('main.index'))

@export_routes.route('/area/<int:area_id>/markdown')
@login_required
def export_area_md(area_id):
    # This function call remains the same
    md_string = export_service.export_area_to_markdown(area_id)
    if md_string:
        area_obj = g.db_session.query(Area.name).filter_by(id=area_id).first()
        area_name_slug = "unknown_area"
        if area_obj:
            area_name_slug = area_obj.name.lower().replace(" ", "_").replace("/", "_")
        filename = f"area_export_{area_name_slug}_{area_id}.md"
        return Response(
            md_string,
            mimetype="text/markdown",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    else:
        flash(f"Failed to export area {area_id} to Markdown. Area may not exist or an error occurred.", "danger")
        return redirect(url_for('areas.view_area', area_id=area_id))