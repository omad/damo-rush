import os

from flask import Flask, render_template
from . import db


def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev", DATABASE=os.path.join(app.instance_path, "rush.db")
    )

    db.init_app(app)

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

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    from .generator import generator as generator_blueprint

    app.register_blueprint(generator_blueprint, url_prefix="/gen")

    return app
