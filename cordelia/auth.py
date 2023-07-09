from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user
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
        # Check if the username, email or phone already exists in the database
        if User.query.filter_by(username=userForm.username.data).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=userForm.email.data).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(phoneNumber=userForm.phoneNumber.data).first():
            flash('Phone number already exists.', 'error')
            return redirect(url_for('auth.register'))

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
            login_user(user, remember=loginForm.remember.data)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('auth.login'))
            
        flash('Invalid username or password.', 'error')
        return redirect(url_for('auth.login'))

    return render_template('login.html', loginForm=loginForm)