import functools

from flask import Blueprint, flash, g, render_template, request, session, url_for
from flask.helpers import redirect
from werkzeug.security import check_password_hash, generate_password_hash

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


def family_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.family_user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.admin"))
        return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    family_id = session.get("family_id")

    if family_id is None:
        g.family_user = None
    else:
        with get_db().cursor() as cursor:
            g.family_user = cursor.execute(
                "SELECT * FROM family_user where family_id = :familyid", (family_id,)
            ).fetchone()


@bp.route("/admin", methods=("GET", "POST"))
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = None
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

        flash(error, category="error")

    return render_template("auth/admin.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    db = get_db()
    states = []
    cities = []
    error = []

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        family_name = request.form["family_name"]
        annual_income = request.form["annual_income"]
        property_count = request.form["property_count"]
        state = request.form["state"]
        district = request.form["district"]
        pincode = request.form["pincode"]

        with db.cursor() as cursor:
            address = cursor.execute(
                "SELECT address_id FROM address where pincode = :pincode",
                (pincode,),
            ).fetchone()

            if address is None:
                error.append({"id": "pincode"})
            else:
                distributor = cursor.execute(
                    "SELECT distributor_id FROM distributor WHERE address_id = :addressid",
                    (address[0],),
                ).fetchone()

                cursor.execute(
                    "INSERT INTO family(family_name, property, address_id, distributor_id) VALUES(:familyname, :property, :addressid,  :distributorid)",
                    (
                        family_name,
                        property_count,
                        address[0],
                        distributor[0],
                    ),
                )

                family_id = cursor.execute(
                    "SELECT family_id FROM family WHERE family_name = :familyname AND property = :property AND address_id = :addressid AND distributor_id = :distributor_id",
                    (
                        family_name,
                        property_count,
                        address[0],
                        distributor[0],
                    ),
                ).fetchone()[0]

                cursor.execute(
                    "INSERT INTO family_user(family_id, username, password) VALUES (:familyid, :username, :password)",
                    (
                        family_id,
                        username,
                        generate_password_hash(password),
                    ),
                )
                db.commit()
                return redirect(url_for("auth.login"))

    with db.cursor() as cursor:
        states = cursor.execute(
            "SELECT * FROM state ORDER BY state_name ASC"
        ).fetchall()
        cities = cursor.execute(
            "SELECT * FROM district ORDER BY district_name ASC"
        ).fetchall()

    return render_template(
        "auth/register.html", states=states, cities=cities, error=error
    )


@bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = None
        error: str | None = None

        with db.cursor() as cursor:
            user = cursor.execute(
                "SELECT * FROM family_user WHERE username = :username", (username,)
            ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user[3], password):
            error = "Incorrect password."

        if error is None and user is not None:
            session.clear()
            session["family_id"] = user[1]
            return redirect(url_for("family.index"))
        elif error is not None:
            flash(error, category="error")
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
