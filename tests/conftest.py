import os
import tempfile
import pytest
from cordelia import create_app
from cordelia.db import db, get_session, close_session
from cordelia.models import User




@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }
    app = create_app(test_config)

    app.config['WTF_CSRF_ENABLED'] = False

    # Before each test, set up the database session and engine
    with app.app_context():
        db.create_all()
        session = get_session(app)
        setattr(app, '_session', session)
        setattr(app, 'db', db)  # Bind the db object to the app

        new_user = User(username='test_admin', email='test_admin@example.com', isAdmin=True)
        new_user.set_password('testpassword')

        db.session.add(new_user)
        db.session.commit()

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



@pytest.fixture
def runner(app):
    return app.test_cli_runner()


    
class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def _get_csrf_token(self):
        with self._client.session_transaction() as sess:
            csrf_token = sess.get('_csrf_token')
        return csrf_token

    def login(self, email='test_admin@example.com', password='testpassword', next=None):
        csrf_token = self._get_csrf_token()

        data = {'email': email, 'password': password, 'csrf_token': csrf_token}
        if next:
            data['next'] = next

        return self._client.post(
            '/auth/login',
            data=data,
            follow_redirects=False if next else True
        )

    def logout(self):
        return self._client.get('/auth/logout')




@pytest.fixture
def auth(client):
    return AuthActions(client)