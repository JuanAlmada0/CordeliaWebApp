import os
from flask import Flask



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'CordeliaDB.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        WTF_CSRF_ENABLED=True,
        SERVER_NAME='127.0.0.1:5000',
        PREFERRED_URL_SCHEME=None
    )
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register the database commands
    from cordelia import db

    # Initialize the database
    db.init_app(app)

    # Import the auth blueprint
    from cordelia import auth

    # Register auth blueprint
    app.register_blueprint(auth.authBp)
    
    # Initialize the LoginManager
    auth.init_app(app)

    # Import the home blueprint
    from cordelia import home

    # Register home blueprint
    app.register_blueprint(home.homeBp)
    
    return app