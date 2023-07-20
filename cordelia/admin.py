from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import current_user
from cordelia.db import db
from cordelia.models import Dress, Rent, User
from cordelia.forms import InventoryForm, SearchForm, RentForm, UpdateForm, DeleteForm
from functools import wraps
import pandas as pd
import os
from datetime import datetime


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
    # Original model columns
    original_model_columns = Dress.__table__.columns.keys()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    inventory_query = Dress.query

    # Initialize the search form
    form = SearchForm(model_columns=original_model_columns)

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data
        model_columns = {column: getattr(Dress, column) for column in original_model_columns}

        if category and filterSearch and category in model_columns:
            column = model_columns[category]
            inventory_query = inventory_query.filter(column.ilike(f"%{filterSearch}%"))

    # After processing the search form, update the rentStatus for Dress Database
    Dress.update_rent_statuses()
    db.session.commit()

    # Paginate the filtered results
    inventory = inventory_query.order_by(Dress.id).paginate(page=page, per_page=items_per_page)

    # Initialize the delete form
    delete_form = DeleteForm()

    # Initialize the maintenance form
    maintenance_form = UpdateForm()

    # Handle form submissions for the delete form
    if delete_form.validate_on_submit():
        dress_id = delete_form.dress_id.data
        return redirect(url_for('admin.delete_dress', dress_id=dress_id))

    # Handle form submissions for the maintenance form
    if maintenance_form.validate_on_submit():
        dress_id = maintenance_form.dress_id.data
        return redirect(url_for('admin.update_maintenance', dress_id=dress_id))

    return render_template('inventory.html', inventory=inventory, form=form, maintenance_form=maintenance_form, delete_form=delete_form, pagination=inventory)


@adminBp.route('/update-dress/<int:dress_id>', methods=['POST'])
@admin_required
def update_maintenance(dress_id):
    dress = Dress.query.get(int(dress_id))
    if dress and not dress.rentStatus:
        dress.update_maintenance_status()
        db.session.commit()
        flash('Dress status changed.', 'success')
    else:
        flash('Dress not available.', 'danger')
    return redirect(url_for('admin.inventory'))


@adminBp.route('/delete/<int:dress_id>', methods=['POST'])
@admin_required
def delete_dress(dress_id):
    dress = Dress.query.get(dress_id)
    if dress and not dress.rentStatus and not dress.maintenanceStatus:
        db.session.delete(dress)
        db.session.commit()
        flash('Dress deleted successfully.', 'success')
    else:
        flash('Dress not available.', 'danger')
    return redirect(url_for('admin.inventory'))


@adminBp.route('/update-Dress', methods=['GET', 'POST'])
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

    return render_template('update.html', form=form, title='Register Dress', action_url=url_for('admin.update'))


@adminBp.route('/rent-inventory', methods=['GET', 'POST'])
@admin_required
def rentInventory():
    model_columns = Rent.__table__.columns.keys()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    inventory_query = Rent.query

    # Initialize the search form
    form = SearchForm(model_columns=model_columns)

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data

        # Map category values to column names
        model_columns = {column: getattr(Rent, column) for column in model_columns}

        if category and filterSearch and category in model_columns:
            column = model_columns[category]
            inventory_query = inventory_query.filter(column.ilike(f"%{filterSearch}%"))

    # Paginate the filtered results
    inventory = inventory_query.order_by(Rent.rentDate.desc()).paginate(page=page, per_page=items_per_page)

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

    return render_template('rentInventory.html', inventory=inventory, form=form, pagination=inventory)


@adminBp.route('/update-Rent', methods=['GET', 'POST'])
@admin_required
def updateRent():

    form = RentForm()

    if form.validate_on_submit():
        dress_id = form.dressId.data
        dress = Dress.query.get(dress_id)

        if not dress.rentStatus and not dress.maintenanceStatus:
            rent = Rent(
                dressId=form.dressId.data,
                clientId=form.userId.data,
                rentDate=form.rentDate.data
            )
            db.session.add(rent)
            db.session.commit()

            flash('Rent added succesfully into the database.')
            return redirect(url_for('admin.rentInventory'))
        else:
            flash('Dress not available.')
    
    return render_template('update.html', form=form, title='Register Rent', action_url=url_for('admin.updateRent'))


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

        model_columns = {column: getattr(User, column) for column in model_columns}

        if category and filterSearch and category in model_columns:
            column = model_columns[category]
            inventory_query = inventory_query.filter(column.ilike(f"%{filterSearch}%"))

    # Paginate the filtered results
    inventory = inventory_query.order_by(User.joinedAtDate.asc()).paginate(page=page, per_page=items_per_page)

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

    return render_template('userInventory.html', inventory=inventory, form=form, pagination=inventory)


@adminBp.route('/download/excel')
@admin_required
def downloadExcell():
    dresses = Dress.query.all()
    users = User.query.all()
    rents = Rent.query.all()

    dress_data = {
        'Dress Id': [dress.id for dress in dresses],
        'Size': [dress.size for dress in dresses],
        'Color': [dress.color for dress in dresses],
        'Style': [dress.style for dress in dresses],
        'Brand': [dress.brand for dress in dresses],
        'Dress Cost': [dress.dressCost for dress in dresses],
        'Market Price': [dress.marketPrice for dress in dresses],
        'Rent Price': [dress.rentPrice for dress in dresses],
        'Rents to Return Investment': [dress.rentsToReturnInvestment for dress in dresses],
        'Times Rented': [dress.timesRented for dress in dresses],
        'Sellable': [dress.sellable for dress in dresses],
        'Rent Status': [dress.rentStatus for dress in dresses]
    }
    user_data = {
        'User Id': [user.id for user in users],
        'Username': [user.username for user in users],
        'Email': [user.email for user in users],
        'Name': [user.name for user in users],
        'Last Name': [user.lastName for user in users],
        'Phone Number': [user.phoneNumber for user in users],
        'Joined At Date': [user.joinedAtDate.strftime('%Y-%m-%d') for user in users],
        'Is Admin': [user.isAdmin for user in users]
    }
    rent_data = {
        'Rent Id': [rent.id for rent in rents],
        'Dress Id': [rent.dressId for rent in rents],
        'User Id': [rent.clientId for rent in rents],
        'Rent Date': [rent.rentDate.strftime('%Y-%m-%d') for rent in rents],
        'Return Date': [rent.returnDate.strftime('%Y-%m-%d') if rent.returnDate else '' for rent in rents],
        'Payment Total': [rent.paymentTotal for rent in rents]
    }

    df_dress = pd.DataFrame(dress_data)
    df_user = pd.DataFrame(user_data)
    df_rent = pd.DataFrame(rent_data)

    instance_path = os.path.join(current_app.instance_path, 'uploads')
    os.makedirs(instance_path, exist_ok=True)

    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    file_name = f'database_data_{current_datetime}.xlsx'

    file_path = os.path.join(current_app.instance_path, 'uploads', file_name)

    # Create the Excel file without the context manager
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as excel_writer:
        df_dress.to_excel(excel_writer, sheet_name='Dresses', index=False)
        df_user.to_excel(excel_writer, sheet_name='Users', index=False)
        df_rent.to_excel(excel_writer, sheet_name='Rents', index=False)

    # Return the file as an attachment
    return send_file(
        file_path,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )