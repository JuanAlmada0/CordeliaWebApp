from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import click
from flask.cli import with_appcontext



# Initialize SQLAlchemy extension
db = SQLAlchemy()


def get_engine():
    # Get the SQLAlchemy engine for the current app
    engine = getattr(current_app, '_engine', None)
    if engine is None:
        # Create a new engine based on the app's database URI
        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
        setattr(current_app, '_engine', engine)
    return engine


def get_session():
    # Get the database session for the current app and engine
    session = getattr(current_app, '_session', None)
    if session is None:
        # Create a scoped session based on the engine
        sessionFactory = scoped_session(sessionmaker(bind=get_engine()))
        session = sessionFactory()
        setattr(current_app, '_session', session)
    return session


def close_session(e=None):
    # Close the database session
    session = getattr(current_app, '_session', None)
    if session is not None:
        session.remove()
        setattr(current_app, '_session', None)


def init_db(app):
    with app.app_context():
        # Create all the database tables based on the defined models
        db.create_all()


@click.command('init-db')
@with_appcontext
def init_db_command():
    # Command to initialize the database
    init_db(current_app)
    click.echo('Initialized the database.')


def init_app(app):
    # Initialize the SQLAlchemy extension for the app
    db.init_app(app)
    # Register the function to close the database session
    app.teardown_appcontext(close_session)
    # Add the init-db command to the app's CLI
    app.cli.add_command(init_db_command)