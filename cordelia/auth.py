from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, db



authBp = Blueprint('auth', __name__, url_prefix='/auth')


@authBp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        lastName = request.form['lastName']
        phoneNumber = request.form['phoneNumber']

        # Check if the username or email already exists in the database
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(phoneNumber=phoneNumber).first():
            flash('Phone number already exists.', 'error')
            return redirect(url_for('auth.register'))
        
        # Create a new user
        user = User(username=username, email=email, name=name, lastName=lastName, phoneNumber=phoneNumber, password_hash=generate_password_hash(password))
        
        # Save the user to the database
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')


@authBp.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


