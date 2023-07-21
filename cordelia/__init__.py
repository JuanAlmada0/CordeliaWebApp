import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'CordeliaDB.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SERVER_NAME='127.0.0.1:5000',
        PREFERRED_URL_SCHEME='http',
        WTF_CSRF_ENABLED=True
    )
    
    csrf = CSRFProtect()
    csrf.init_app(app)

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

    # Import blueprints
    from cordelia import auth
    from cordelia import admin
    from cordelia import home
    
    # Register blueprintS
    app.register_blueprint(auth.authBp)
    app.register_blueprint(admin.adminBp)
    app.register_blueprint(home.homeBp)
    
    # Initialize the LoginManager
    auth.init_app(app)

    return app