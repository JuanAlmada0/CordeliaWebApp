from flask import Blueprint, render_template, redirect, url_for, flash, request
from cordelia.models import db, User
from cordelia.forms import UserRegistrationForm



authBp = Blueprint('auth', __name__, url_prefix='/auth')


@authBp.route('/register', methods=['GET', 'POST'])
def register():

    userForm = UserRegistrationForm()

    if userForm.validate_on_submit():
        # Check if the username, email or phone already exists in the database
        existing_user = User.query.filter_by(username=userForm.username.data).first()

        if existing_user:
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))

        existing_email = User.query.filter_by(email=userForm.email.data).first()
        if existing_email:
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.register'))

        existing_phone = User.query.filter_by(phoneNumber=userForm.phoneNumber.data).first()
        if existing_phone:
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


@authBp.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')