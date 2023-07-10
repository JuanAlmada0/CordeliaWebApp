from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, abort
)
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.urls import url_parse
from cordelia.models import db, User
from cordelia.forms import RegistrationForm, LoginForm


# Create auth blueprint
authBp = Blueprint('auth', __name__, url_prefix='/auth')

# Create login manager instance
login_manager = LoginManager()

# Register route
@authBp.route('/register', methods=['GET', 'POST'])
def register():

    userForm = RegistrationForm()

    if userForm.validate_on_submit():
        # Create new User
        user = User(
            username=userForm.username.data, 
            email=userForm.email.data, 
            name=userForm.name.data, 
            lastName=userForm.lastName.data,
            phoneNumber=userForm.phoneNumber.data
        )
        user.set_password(userForm.password.data)
        
        # Save the user to the database
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', userForm=userForm)

# Initialize login manager
def init_app(app):
    login_manager.init_app(app)

# User loader
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

# Login route
@authBp.route('/login', methods=['GET', 'POST'])
def login():
    loginForm = LoginForm()

    if loginForm.validate_on_submit():
        user = User.query.filter_by(email=loginForm.email.data).first()

        if user and user.check_password(loginForm.password.data):
            # Log the user in by storing their ID in the user's session
            login_user(user, remember=loginForm.remember.data)

            flash('Logged in successfully.', 'success')

            next_page = request.args.get('next')
            # Check if the network location is valid for next_page
            if next_page and url_parse(next_page).netloc:
                return abort(400)
            
            return redirect(next_page) if next_page else redirect(url_for('home.home'))
            
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.login'))

    return render_template('login.html', loginForm=loginForm)

# Logout route
@authBp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/home')