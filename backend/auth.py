import functools
from typing import Any

from flask import Blueprint, flash, g, render_template, request, session, url_for
from flask.helpers import redirect
from werkzeug.security import check_password_hash

from backend.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_admin():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        with get_db().cursor() as cursor:
            g.user = cursor.execute(
                "SELECT * FROM admin WHERE user_id = :userid", (user_id,)
            ).fetchone()


@bp.before_app_request
def load_logged_in_user():
    family_id = session.get("family_id")

    if family_id is None:
        g.user = None
    else:
        with get_db().cursor() as cursor:
            g.user = cursor.execute(
                "SELECT * FROM family_user where family_id = :familyid", (family_id,)
            ).fetchone()


@bp.route("/admin", methods=("GET", "POST"))
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user: None = None
        error: str | None = None

        with db.cursor() as cursor:
            user = cursor.execute(
                "SELECT * FROM admin WHERE username = :username", (username,)
            ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user[2], password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user[0]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/admin.html")


@bp.route("/register")
def register():
    return "blank"


@bp.route("/login")
def login():
    return "blank"


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
