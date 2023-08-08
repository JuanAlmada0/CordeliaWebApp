import os
import tempfile
import pytest
from cordelia import create_app
from cordelia.db import db, get_session, close_session




@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }
    app = create_app(test_config)

    # Before each test, set up the database session and engine
    with app.app_context():
        db.create_all()
        session = get_session(app)
        setattr(app, '_session', session)

    yield app

    # After each test, close the database session and dispose of the engine
    with app.app_context():
        close_session()
        db.session.remove()  # Explicitly remove the session
        db.engine.dispose()  # Dispose of the engine

    # Clean up the temporary database file after the test
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except PermissionError:
        pass  # Ignore the error if the file is still being used



@pytest.fixture
def client(app):
    return app.test_client()