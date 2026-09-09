from flask import Blueprint, render_template

from backend.db import get_db


bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("index")
def index():
    items = []
    families = []
    with get_db().cursor() as cursor:
        items = cursor.execute("SELECT * FROM item").fetchall()
        families = cursor.execute("SELECT * FROM family").fetchall()
    return render_template("admin/admin.html", items=items, families=families)
