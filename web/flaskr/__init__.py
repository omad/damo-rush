import os

from flask import Flask
from mkdb import create_db


def create_app(test_config=None):
    instance_path = os.path.join(os.path.abspath('.'), 'instance')

    # Ensure the instance folder exists
    try:
        os.makedirs(instance_path)
    except OSError:
        pass

    # Create database if not existing
    create_db('../cli/rush.txt', os.path.join(instance_path, 'rush.db'))

    # Create and configure the app
    app = Flask(__name__, instance_path=instance_path)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'rush.db'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        #app.config.from_pyfile('config.py', silent=False)
        pass
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)


    # a simple page that says hello
    @app.route('/')
    def homepage():
        return '<a href="/hello">hello</a>'

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
