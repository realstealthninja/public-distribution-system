import os

from flask import Flask, render_template
from flask_bootstrap import Bootstrap5

from backend import family

from . import auth, db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev", DATABASE="hello")

    bootstrap = Bootstrap5(app)

    db.init_app(app)

    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/")
    def index():
        family_count = ()
        state_count = ()
        allocation_count = ()

        with db.get_db().cursor() as cursor:
            family_count = cursor.execute(
                "SELECT COUNT(family_id) FROM family"
            ).fetchone()
            state_count = cursor.execute("SELECT COUNT(state_id) FROM state").fetchone()
            allocation_count = cursor.execute(
                "SELECT COUNT(allocation_id) FROM allocation"
            ).fetchone()
        return render_template(
            "index.html",
            family_count=str(family_count[0]),
            state_count=str(state_count[0]),
            allocation_count=str(allocation_count[0]),
        )

    app.register_blueprint(auth.bp)
    app.register_blueprint(family.bp)
    app.add_url_rule("/", endpoint="index")
    return app
