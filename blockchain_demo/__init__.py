from flask import Flask
from flask_socketio import SocketIO

socket_io = SocketIO()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='secret!',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    from blockchain_demo.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.add_url_rule('/', endpoint='blockchain_index')

    socket_io.init_app(app)
    return app
