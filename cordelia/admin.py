from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from cordelia.db import db, get_session
from cordelia.models import Dress
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
    session = get_session()

    # Get the column names from the Dress model
    model_columns = Dress.__table__.columns.keys()

    # Pass the model_columns list to the SearchForm constructor
    form = SearchForm(model_columns=model_columns)

    inventory = session.query(Dress).all()

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data

        # Map category values to column names
        category_to_column = {column: getattr(Dress, column) for column in model_columns}

        if category and filterSearch and category in category_to_column:
            column = category_to_column[category]
            inventory = session.query(Dress).filter(column.ilike(f"%{filterSearch}%")).all()

    return render_template('inventory.html', inventory=inventory, form=form)



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
            dressDescription = form.description.data,
            boughtPrice = form.boughtPrice.data,
            marketPrice = form.marketPrice.data,
            rentPrice = form.rentPrice.data,
        )
        db.session.add(dress)
        db.session.commit()

        flash('Dress added succesfully into the database.')
        return redirect(url_for('admin.inventory'))
    
    return render_template('update.html', form=form)