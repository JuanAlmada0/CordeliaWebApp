from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import click
from flask.cli import with_appcontext


# Initialize SQLAlchemy extension
db = SQLAlchemy()


def get_engine(app):
    # Get the SQLAlchemy engine for the current app
    engine = getattr(app, '_engine', None)
    if engine is None:
        # Create a new engine based on the app's database URI
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        setattr(app, '_engine', engine)
    return engine


def get_session(app):
    # Get the database session for the current app and engine
    session = getattr(app, '_session', None)
    if session is None:
        # Create a scoped session based on the engine
        sessionFactory = scoped_session(sessionmaker(bind=get_engine(app)))
        session = sessionFactory()
        setattr(app, '_session', session)
    return session


def close_session(e=None):
    # Close the database session
    app = current_app._get_current_object()
    session = getattr(app, '_session', None)
    if session is not None:
        session.close()
        setattr(app, '_session', None)


def init_db(app):
    with app.app_context():
        # Create all the database tables based on the defined models
        db.create_all()

        # Create admin user
        from cordelia.models import User
        admin_user = User(
            username='Admin',
            email='admin@example.com',
            name='Admin',
            lastName='Example',
            phoneNumber='526443569870',
            isAdmin=True
        )
        admin_user.set_password('password1234')

        db.session.add(admin_user)
        db.session.commit()


# Command to initialize the database
@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db(current_app)
    click.echo('Initialized the database.')
    

# Command to populate the database with sample data.
@click.command('populate-db')
@with_appcontext
def populate_db_command():
    from cordelia.sample_db import populate_db
    with current_app.app_context():
        populate_db()
        click.echo('Updated the database.')


def init_app(app):
    # Initialize the SQLAlchemy extension for the app
    db.init_app(app)
    # Register the function to close the database session
    app.teardown_appcontext(close_session)
    # Add the init-db command to the app's CLI
    app.cli.add_command(init_db_command)
    # Add the populate-db command to the app's CLI
    app.cli.add_command(populate_db_command)