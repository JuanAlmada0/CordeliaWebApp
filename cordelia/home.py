from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from cordelia.db import db, get_session
from cordelia.models import Dress, User, Rent



homeBp = Blueprint('home', __name__)


@homeBp.route('/')
@homeBp.route('/home')
def home():
    return render_template('home.html')


@homeBp.route('/catalog')
def catalog():
    
    session = get_session()

    inventory = session.query(Dress).all()

    return render_template('catalog.html', inventory=inventory)


@homeBp.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():

    return render_template('cart.html')