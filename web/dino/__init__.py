import os

from flask import Flask, render_template, send_from_directory, jsonify
from . import db, graphics


class CustomFlask(Flask):
    # Allow jinja / vuejs templating together
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(variable_start_string="[[", variable_end_string="]]"))


def create_app(test_config=None):
    # Create and configure the app
    app = CustomFlask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev", DATABASE=os.path.join(app.instance_path, "rush.db")
    )

    db.init_app(app)
    graphics.init_app(app)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if test_config is None:
        # load the instance config, if it exists, when not testing
        # app.config.from_pyfile('config.py', silent=False)
        pass
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # a simple page that says hello
    @app.route("/")
    def homepage():
        return render_template("index.html")

    @app.route("/credits")
    def credits():
        return render_template("credits.html")

    @app.route("/stats")
    def stats():
        return render_template("stats.html")

    @app.route("/api/stats")
    def api_stats():
        conn = db.get_db()
        c = conn.cursor()
        c.execute("select * from dl_count")

        data = [dict(row) for row in c.fetchall()]
        total = sum(row["nb"] for row in data)
        return jsonify({"total":total, "list":data})

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )

    from .generator import generator as generator_blueprint

    app.register_blueprint(generator_blueprint, url_prefix="/gen")

    return app
