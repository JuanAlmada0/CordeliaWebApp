from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from cordelia.db import db
from cordelia.models import Dress, Rent
from cordelia.forms import UserRentForm


homeBp = Blueprint('home', __name__)


@homeBp.route('/')
@homeBp.route('/home')
def home():
    return render_template('home.html')


@homeBp.route('/catalog')
def catalog():
    inventory = Dress.query.all()

    return render_template('home_views/catalog.html', inventory=inventory)


@homeBp.route('/cart/<int:dress_id>', methods=['GET', 'POST'])
@login_required
def cart(dress_id):
    user = current_user
    dress = Dress.query.get(dress_id)

    if not dress:
        flash('Dress not found.', 'danger')
        return redirect(url_for('home.catalog'))
    
    form = UserRentForm()

    if form.validate_on_submit():
        rent = Rent(
            dressId=dress.id,
            clientId=user.id,
            rentDate=form.rentDate.data
        )
        db.session.add(rent)
        db.session.commit()

        flash('Dress added to cart.', 'success')
        return redirect(url_for('home.checkout', rent_id=rent.id))

    return render_template('home_views/cart.html', dress=dress, form=form) 


@homeBp.route('/checkout/<int:rent_id>', methods=['GET', 'POST'])
@login_required
def checkout(rent_id):
    rent = Rent.query.get(rent_id)
    
    return render_template('home_views/checkout.html', rent=rent)