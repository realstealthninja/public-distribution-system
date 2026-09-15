from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)

from backend.auth import admin_required
from backend.db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_required
@bp.route("allocation", methods=["POST"])
def allocation():
    familyid = request.form["familyid"]
    itemid = request.form["itemid"]
    amount = request.form["amount"]
    price = request.form["price"]
    date = request.form["date"]
    with get_db().cursor() as cursor:
        cursor.execute(
            "INSERT INTO allocation(family_id, item_id, amount, price, allocation_date) VALUES (:familyid, :itemid, :amount, :price, TO_DATE(:adate, 'YYYY-MM-DD'))",
            (
                familyid,
                itemid,
                amount,
                price,
                date,
            ),
        )
    get_db().commit()

    return redirect(url_for("admin.index"))


@admin_required
@bp.route("inventory/<id>", methods=["DELETE"])
def deleteInventory(id):
    with get_db().cursor() as cursor:
        cursor.execute("DELETE FROM inventory WHERE inventory_id = :id", (id,))
    get_db().commit()
    return redirect(url_for("admin.index"))


@admin_required
@bp.route("family/<id>", methods=["DELETE"])
def deleteFamily(id):
    with get_db().cursor() as cursor:
        cursor.execute("DELETE FROM family WHERE family_id = :id", (id,))
    get_db().commit()
    return redirect(url_for("admin.index"))


@admin_required
@bp.route("allocation/<id>", methods=["DELETE"])
def deleteAllocation(id):
    with get_db().cursor() as cursor:
        cursor.execute("DELETE FROM allocation WHERE allocation_id = :id", (id,))
    get_db().commit()
    return redirect(url_for("admin.index"))


@admin_required
@bp.route("item/<id>", methods=["DELETE"])
def deleteItem(id):
    with get_db().cursor() as cursor:
        cursor.execute("DELETE FROM item WHERE item_id = :id", (id,))
    get_db().commit()
    return redirect(url_for("admin.index"))


@admin_required
@bp.route("item", methods=["POST"])
def item():
    name = request.form["item"]
    with get_db().cursor() as cursor:
        cursor.execute("INSERT INTO item(name) VALUES(:name)", (name,))
    get_db().commit()
    return redirect(url_for("admin.index"))


@admin_required
@bp.route("inventory", methods=["POST"])
def inventory():
    distributor = request.form["distributor"]
    item = request.form["item"]
    amount = request.form["amount"]
    with get_db().cursor() as cursor:
        cursor.execute(
            "INSERT INTO inventory(distributor_id, item_id, amount) VALUES (:distid, :itemid, :amount)",
            (
                distributor,
                item,
                amount,
            ),
        )
    get_db().commit()

    return redirect(url_for("admin.index"))


@admin_required
@bp.route("/", methods=["GET"])
def index():
    items = []
    families = []
    allocations = []
    distributors = []
    inventories = []

    with get_db().cursor() as cursor:
        items = cursor.execute("SELECT * FROM item").fetchall()
        families = cursor.execute("SELECT * FROM family").fetchall()
        allocations = cursor.execute(
            "SELECT allocation_id, family_name, name, amount, price, TO_CHAR(allocation_date, 'DD-MON-YYYY') FROM allocation NATURAL JOIN item NATURAL JOIN family ORDER BY allocation_id"
        ).fetchall()
        distributors = cursor.execute(
            "SELECT distributor_id, distributor_name FROM distributor WHERE distributor_id in (SELECT distributor_id FROM family)"
        ).fetchall()
        inventories = cursor.execute(
            "SELECT inventory_id, distributor_name, item.name, amount  FROM inventory NATURAL JOIN distributor NATURAL JOIN item ORDER BY distributor_name"
        ).fetchall()

    return render_template(
        "admin/admin.html",
        items=items,
        families=families,
        allocations=allocations,
        distributors=distributors,
        inventories=inventories,
    )
