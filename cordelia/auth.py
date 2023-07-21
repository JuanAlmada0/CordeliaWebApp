from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, session
)
from flask_login import LoginManager, login_user, login_required, logout_user
from urllib.parse import urlparse, urljoin 
from cordelia.models import db, User
from cordelia.forms import RegistrationForm, LoginForm


# Create auth blueprint
authBp = Blueprint('auth', __name__, url_prefix='/auth')


# Create login manager instance
login_manager = LoginManager()


# Initialize login manager
def init_app(app):
    login_manager.init_app(app)


# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Set the login view
login_manager.login_view = 'auth.login'


def is_safe_url(target):
    """
    Checks if the target URL is safe by comparing its scheme and netloc with the current request's URL.

    :param target: The target URL to validate.
    :return: True if the target URL is safe, False otherwise.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


# Register route
@authBp.route('/register', methods=['GET', 'POST'])
def register():

    form = RegistrationForm()

    if form.validate_on_submit():
        # Create new User
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            name=form.name.data, 
            lastName=form.lastName.data,
            phoneNumber=form.phoneNumber.data
        )
        user.set_password(form.password.data)
        
        # Save the user to the database
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('authenticate.html', form=form, title='Registration', action_url=url_for('auth.register'))


# Login route
@authBp.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()

    next_page = session.get('next_page')

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            # Log the user in by storing their ID in the user's session
            login_user(user, remember=form.remember.data)

            flash('Logged in successfully.', 'success')

            if user.isAdmin:
                return redirect(url_for('admin.inventory'))
            else:
                if next_page and is_safe_url(next_page):
                    session.pop('next_page')
                    return redirect(next_page)
                else:
                    return redirect(url_for('home.home'))
           
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.login'))

    session['next_page'] = request.referrer

    return render_template('authenticate.html', form=form, title='Login', action_url=url_for('auth.login'))


# Logout route
@authBp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've been logged out", 'message')
    return redirect(url_for('home.home'))