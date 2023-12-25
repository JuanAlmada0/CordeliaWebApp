import os
from flask import Flask
import secrets

import logging


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY=secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'CordeliaDB.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SERVER_NAME='127.0.0.1:5000',
        PREFERRED_URL_SCHEME='https',
        WTF_CSRF_ENABLED=True,
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

    # Import blueprints
    from cordelia import auth
    from cordelia.admin import admin
    from cordelia import home
    from cordelia.api import api_inventory, api_transactions
    
    # Register blueprints
    app.register_blueprint(auth.authBp)
    app.register_blueprint(admin.adminBp)
    app.register_blueprint(home.homeBp)
    app.register_blueprint(api_inventory.api_inventory_bp)
    app.register_blueprint(api_transactions.api_transactions_bp)
    
    # Initialize the LoginManager
    auth.init_app(app)

    log_dir = os.path.join(app.instance_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file_path = os.path.join(log_dir, 'debug.log')

    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(), 
                        logging.FileHandler(log_file_path, mode='w')
                    ])

    return app