from flask import Blueprint, Response, g, render_template, request
from flask_wtf import FlaskForm
from wtforms import IntegerField, Label, StringField, SubmitField

from backend.auth import family_required
from backend.db import get_db

bp = Blueprint("family", __name__, url_prefix="/family")


class MemberForm(FlaskForm):
    name = StringField("Name")
    age = IntegerField("Age")
    submit = SubmitField("+")


@bp.route("/member/<id>", methods=["DELETE"])
@family_required
def deleteMember(id):
    with get_db().cursor() as cursor:
        cursor.execute("DELETE FROM members WHERE member_id = :memberid", (id,))
    get_db().commit()
    return Response(None, 200)


@bp.route("/", methods=["GET", "POST"])
@family_required
def index():
    form = MemberForm(request.form)
    family = ()
    family_id = g.family_user[1]
    members = [()]

    if request.method == "POST":
        with get_db().cursor() as cursor:
            cursor.execute(
                "INSERT INTO members(family_id, name, age) VALUES (:familyid, :name, :age)",
                (
                    family_id,
                    form.name.data,
                    form.age.data,
                ),
            )
        get_db().commit()

    with get_db().cursor() as cursor:
        family = cursor.execute(
            "SELECT * FROM family WHERE family_id = :familyid", (family_id,)
        ).fetchone()

        members = cursor.execute(
            "SELECT * FROM members WHERE family_id = :familyid", (family_id,)
        ).fetchall()

        distributor = cursor.execute(
            "SELECT * FROM distributor WHERE distributor_id = :distributorid",
            (family[4],),
        ).fetchone()
        address = cursor.execute(
            "SELECT a.pincode, d.district_name, s.state_name FROM address a JOIN district d ON(a.district_id = d.district_id) JOIN state s ON(d.state_id = s.state_id)  WHERE address_id = :addressid",
            (family[5],),
        ).fetchone()
    return render_template(
        "family/family.html",
        family=family,
        members=members,
        form=form,
        distributor_name=distributor[1],
        pincode=address[0],
        district=address[1],
        state=address[2],
    )


@bp.route("/allocations")
@family_required
def allocations():
    return "un implemented"


@bp.route("/transactions")
@family_required
def transactions():
    return "unimplemented"


@bp.route("/order")
@family_required
def order():
    return "Unimplemented"
