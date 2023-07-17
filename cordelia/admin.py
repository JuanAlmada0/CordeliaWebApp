from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from cordelia.db import db
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
    # Get the column names from the Dress model
    model_columns = Dress.__table__.columns.keys()

    # Pass the model_columns list to the SearchForm constructor
    form = SearchForm(model_columns=model_columns)

    inventory = Dress.query.all()

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data

        # Map category values to column names
        category_to_column = {column: getattr(Dress, column) for column in model_columns}

        if category and filterSearch and category in category_to_column:
            column = category_to_column[category]
            inventory = Dress.query.filter(column.ilike(f"%{filterSearch}%")).all()

    # Handles the DELETE button for inventory.
    if request.method == 'POST':
        dress_id = request.form.get('dress_id')

        if dress_id:
            dress = Dress.query.get(int(dress_id))

            if dress:
                db.session.delete(dress)
                db.session.commit()
                flash('Dress deleted successfully.', 'success')
                return redirect(url_for('admin.inventory'))
            else:
                flash('Dress not found.', 'danger')

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
            dressCost = form.dressCost.data,
            marketPrice = form.marketPrice.data,
            rentPrice = form.rentPrice.data,
        )
        db.session.add(dress)
        db.session.commit()

        flash('Dress added succesfully into the database.')
        return redirect(url_for('admin.inventory'))
    
    return render_template('update.html', form=form)