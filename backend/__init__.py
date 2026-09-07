import os

from flask import Flask, render_template

from flask_bootstrap import Bootstrap5

from . import auth, db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev", DATABASE="hello")

    bootstrap = Bootstrap5(app)

    db.init_app(app)

    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/")
    def index():
        return render_template("index.html")

    app.register_blueprint(auth.bp)
    return app
