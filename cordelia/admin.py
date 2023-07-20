from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from flask_paginate import Pagination
from cordelia.db import db
from cordelia.models import Dress, Rent, User
from cordelia.forms import InventoryForm, SearchForm
from functools import wraps



adminBp = Blueprint('admin', __name__, url_prefix='/admin')


# admin_required Wrapper
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.isAdmin:
            flash('This page requires Admin Access', 'message')
            return redirect(url_for('home.home'))
        return f(*args, **kwargs)
    return decorated_function


@adminBp.route('/inventory', methods=['GET', 'POST'])
@admin_required
def inventory():
    # Get the column names from the Dress model
    model_columns = Dress.__table__.columns.keys()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    inventory_query = Dress.query

    # Initialize the search form
    form = SearchForm(model_columns=model_columns)

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data
        # Map category values to column names
        category_to_column = {column: getattr(Dress, column) for column in model_columns}
        if category and filterSearch and category in category_to_column:
            column = category_to_column[category]
            inventory_query = inventory_query.filter(column.ilike(f"%{filterSearch}%"))

    # After processing the search form, update the rentStatus for Dress Database
    Dress.update_rent_statuses()
    db.session.commit()

    # Paginate the results after applying search filters
    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    # Handles the DELETE button for inventory.
    if request.method == 'POST':
        dress_id = request.form.get('dress_id')
        if dress_id:
            dress = Dress.query.get(int(dress_id))
            if dress and not dress.rentStatus:
                db.session.delete(dress)
                db.session.commit()
                flash('Dress deleted successfully.', 'success')
                return redirect(url_for('admin.inventory'))
            else:
                flash('Dress not found.', 'danger')

    pagination = Pagination(page=page, per_page=items_per_page, total=inventory_query.count(), css_framework='bootstrap4')

    return render_template('inventory.html', inventory=inventory, form=form, pagination=pagination)


@adminBp.route('/update', methods=['GET', 'POST'])
@admin_required
def update():

    form = InventoryForm()

    if form.validate_on_submit():

        dress = Dress(
            brand = form.brand.data,
            size = form.size.data,
            color = form.color.data,
            style = form.style.data,
            dressCost = form.dressCost.data,
            marketPrice = form.marketPrice.data,
            rentPrice = form.rentPrice.data,
        )
        db.session.add(dress)
        db.session.commit()

        flash('Dress added succesfully into the database.')
        return redirect(url_for('admin.inventory'))
    
    return render_template('update.html', form=form)


@adminBp.route('/rent-inventory', methods=['GET', 'POST'])
@admin_required
def rentInventory():
    model_columns = Rent.__table__.columns.keys()

    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    inventory_query = Rent.query

    form = SearchForm(model_columns=model_columns)

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data

        # Map category values to column names
        category_to_column = {column: getattr(Rent, column) for column in model_columns}

        if category and filterSearch and category in category_to_column:
            column = category_to_column[category]
            inventory_query = inventory_query.filter(column.ilike(f"%{filterSearch}%"))

    # Modify the query to order by the newest rent (rent.rentday column)
    inventory_query = inventory_query.order_by(Rent.rentDate.desc())

    # Paginate the filtered results
    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    # Handles the DELETE button for inventory.
    if request.method == 'POST':
        rent_id = request.form.get('rent_id')
        if rent_id:
            rent = Rent.query.get(int(rent_id))
            if rent and rent.is_returned():
                # Store dress ID before deleting rent object
                dress_id = rent.dressId
                db.session.delete(rent)
                db.session.commit()

                try:
                    # Attempt to find the associated dress and decrement times_rented
                    associated_dress = Dress.query.get(dress_id)
                    if associated_dress:
                        associated_dress.decrement_times_rented()
                        db.session.commit()
                    else:
                        # Handle the case when the associated dress is not found
                        flash('Associated Dress not found when trying to decrement times_rented.', 'danger')
                except Exception as e:
                    # Handle any unexpected errors that might occur during the process
                    flash(f'Error: {str(e)}', 'danger')

                flash('Rent deleted successfully.', 'success')
                return redirect(url_for('admin.rentInventory'))
            else:
                flash('Rent not found.', 'danger')

    pagination = Pagination(page=page, per_page=items_per_page, total=inventory_query.count(), css_framework='bootstrap4')

    return render_template('rentInventory.html', inventory=inventory, form=form, pagination=pagination)


@adminBp.route('/user-inventory', methods=["GET", "POST"])
@admin_required
def userInventory():
    model_columns = User.__table__.columns.keys()

    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    inventory_query = User.query

    form = SearchForm(model_columns=model_columns)

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data

        category_to_column = {column: getattr(User, column) for column in model_columns}

        if category and filterSearch and category in category_to_column:
            column = category_to_column[category]
            inventory_query = inventory_query.filter(column.ilike(f"%{filterSearch}%"))
    
    inventory_query = inventory_query.order_by(User.joinedAtDate.asc())

    # Paginate the filtered results
    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    # Handles the DELETE button for inventory.
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id:
            user = User.query.get(int(user_id))
            if user and not user.check_status():
                # Store dress ID before deleting rent object
                db.session.delete(user)
                db.session.commit()

                flash('User deleted successfully.', 'success')
                return redirect(url_for('admin.userInventory'))
            else:
                flash('User not found, or busy.', 'danger')

    pagination = Pagination(page=page, per_page=items_per_page, total=inventory_query.count(), css_framework='bootstrap4')

    return render_template('userInventory.html', inventory=inventory, form=form, pagination=pagination)