from flask import Blueprint, Response, flash, g, render_template, request
from flask_wtf import FlaskForm
from oracledb import DatabaseError, Error
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
    allocation_count = 0
    transcation_count = 0
    items = []
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
        allocation_count = str(
            cursor.execute(
                "SELECT COUNT(allocation_id) FROM allocation WHERE family_id = :familyid",
                (family_id,),
            ).fetchone()[0]
        )
        transcation_count = str(
            cursor.execute(
                "SELECT COUNT(transaction_id) FROM transaction WHERE family_id = :familyid ",
                (family_id,),
            ).fetchone()
        )
        items = map(
            lambda x: f"{x[0]} - {x[1]} kg",
            cursor.execute(
                "SELECT name, SUM(NVL(amount, 0)) FROM allocation a RIGHT OUTER JOIN item i ON (i.item_id = a.item_id) GROUP BY name"
            ).fetchall(),
        )

    return render_template(
        "family/family.html",
        family=family,
        members=members,
        form=form,
        distributor_name=distributor[1],
        pincode=address[0],
        district=address[1],
        state=address[2],
        allocation_count=allocation_count,
        transcation_count=transcation_count,
        items=items,
    )


@bp.route("/allocations")
@family_required
def allocations():
    allocations = []
    with get_db().cursor() as cursor:
        allocations = cursor.execute(
            "SELECT TO_CHAR(allocation_date, 'DD-MON-YYYY'), name, amount, price FROM allocation NATURAL JOIN ITEM WHERE family_id = :familyid ORDER BY allocation_date",
            (g.family_user[1],),
        ).fetchall()
    return render_template("family/allocations.html", allocations=allocations)


@bp.route("/transactions")
@family_required
def transactions():
    transactions = []
    with get_db().cursor() as cursor:
        query = """--sql
        SELECT TO_CHAR(transaction_time, 'DD-MON-YYYY HH:mm:SS'),
                name,
                amount,
                bill
                FROM transaction NATURAL JOIN allocation NATURAL JOIN item
                WHERE family_id = :familyid
        """
        transactions = cursor.execute(query, (g.family_user[1],)).fetchall()

    return render_template("family/transactions.html", transactions=transactions)


@bp.route("/order", methods=["GET", "POST"])
@family_required
def order():
    allocations = []

    if request.method == "POST":
        alloc_id = request.form["allocation"]
        amount = request.form["amount"]
        try:
            with get_db().cursor() as cursor:
                cursor.execute(
                    "UPDATE allocation SET amount = amount - :amount WHERE allocation_id = :alloc_id",
                    (
                        amount,
                        alloc_id,
                    ),
                )
                cursor.execute(
                    """--sql--

                UPDATE inventory SET amount = amount - :amount WHERE
                    item_id = (SELECT item_id FROM allocation WHERE allocation_id = :alloc_id)
                    AND distributor_id = (SELECT distributor_id FROM family WHERE family_id = :family_id)
                """,
                    amount=amount,
                    alloc_id=alloc_id,
                    family_id=g.family_user[0],
                )
                cursor.execute(
                    """--sql--

                    INSERT INTO transaction(
                                family_id,
                                allocation_id,
                                transaction_time,
                                amount,
                                bill
                    ) VALUES (
                        :familyid,
                        :alloc_id,
                        LOCALTIMESTAMP,
                        :amount,
                        (
                            SELECT ROUND(price * :amount, 2) FROM allocation 
                            WHERE allocation_id = :alloc_id
                        )
                    )""",
                    familyid=g.family_user[0],
                    alloc_id=alloc_id,
                    amount=amount,
                )
            get_db().commit()
            print("hello")
        except Error as sqlerror:
            get_db().rollback()
            (error,) = sqlerror.args
            flash(error.message)

    with get_db().cursor() as cursor:
        allocations = cursor.execute(
            "SELECT allocation_id, name, amount, price FROM allocation NATURAL JOIN ITEM WHERE family_id = :familyid AND amount > 0 ORDER BY allocation_date",
            (g.family_user[1],),
        ).fetchall()

    return render_template("family/order.html", allocations=allocations)
