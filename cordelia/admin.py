from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from cordelia.db import db
from cordelia.models import Dress, Rent, User
from cordelia.forms import SearchForm, DressForm, RentForm, UserForm, MaintenanceForm, DeleteForm
from functools import wraps
import json
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
        
        model_columns = {column: getattr(Dress, column) for column in model_columns}

        if category and filterSearch and category in model_columns:
            column = model_columns[category]
            inventory_query = inventory_query.filter(column.ilike(f"%{filterSearch}%"))

    # After processing the search form, update the rentStatus for Dress Database
    Dress.update_rent_statuses()
    db.session.commit()

    # Paginate the filtered results
    inventory = inventory_query.order_by(Dress.rentStatus.desc(), Dress.maintenanceStatus.desc()).paginate(page=page, per_page=items_per_page)

    # Initialize the delete form
    delete_form = DeleteForm()

    # Initialize the maintenance form
    maintenance_form = MaintenanceForm()

    # Handle form submissions for the delete form
    if delete_form.validate_on_submit():
        dress_id = delete_form.dress_id.data
        return redirect(url_for('admin.delete_object', dataBase='Dress', id=dress_id))

    # Handle form submissions for the maintenance form
    if maintenance_form.validate_on_submit():
        dress_id = maintenance_form.dress_id.data
        return redirect(url_for('admin.update_maintenance', dress_id=dress_id))

    return render_template('admin_views/inventory.html', inventory=inventory, form=form, maintenance_form=maintenance_form, delete_form=delete_form, pagination=inventory)



@adminBp.route('/update-dress/<int:dress_id>', methods=['POST'])
@admin_required
def update_maintenance(dress_id):
    dress = Dress.query.get(int(dress_id))

    if dress and not dress.rentStatus:
        # Update maintenance status
        dress.update_maintenance_status()
        
        # Get the maintenance data from the form
        maintenance_date = request.form.get("maintenanceDate")
        maintenance_cost = request.form.get("maintenanceCost")

        # Generate the current date if not provided
        if not maintenance_date:
            maintenance_date = datetime.today().strftime('%Y-%m-%d')

        try:
            # Convert cost to integer
            maintenance_cost = int(maintenance_cost)
        except ValueError:
            flash('Invalid maintenance cost. Please enter a valid number.', 'danger')
            return redirect(url_for('admin.inventory'))

        # Get the existing maintenance log data (if any) from the dress
        existing_maintenance_log = json.loads(dress.maintenanceLog) if dress.maintenanceLog else []

        # Append the new maintenance data to the existing log
        new_maintenance_data = {
            "date": maintenance_date,
            "cost": maintenance_cost
        }
        existing_maintenance_log.append(new_maintenance_data)

        # Save the updated maintenance log to the dress
        dress.maintenanceLog = json.dumps(existing_maintenance_log)
        db.session.commit()

        flash('Dress maintenance record added successfully.', 'success')
    else:
        flash('Dress not available or already rented.', 'danger')

    flash('Maintenance updated successfully!', 'success')
    return redirect(url_for('admin.inventory'))



@adminBp.route("/update-maintenance-status/<int:dress_id>", methods=["POST"])
@admin_required
def update_maintenance_status(dress_id):
    dress = Dress.query.get(dress_id)

    if dress:
        dress.update_maintenance_status()
        db.session.commit()
        flash("Maintenance status updated successfully!", 'success')
    else:
        flash("Dress not found!", 'error')

    return redirect(url_for('admin.inventory'))



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

    # Initialize the delete form
    delete_form = DeleteForm()

    # Handles the DELETE button for inventory.
    if delete_form.validate_on_submit():
        rent_id = delete_form.rent_id.data
        return redirect(url_for('admin.delete_object', dataBase='Rent', id=rent_id))

    return render_template('admin_views/rentInventory.html', inventory=inventory, form=form, delete_form=delete_form, pagination=inventory)



@adminBp.route('/user-inventory', methods=["GET", "POST"])
@admin_required
def userInventory():
    model_columns = User.__table__.columns.keys()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    inventory_query = User.query

    # Initialize the search form
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

    # Initialize the delete form
    delete_form = DeleteForm()

    # Handles the DELETE button for inventory.
    if delete_form.validate_on_submit():
        user_id = delete_form.user_id.data
        return redirect(url_for('admin.delete_object', dataBase='User', id=user_id))

    return render_template('admin_views/userInventory.html', inventory=inventory, form=form, delete_form=delete_form, pagination=inventory)



@adminBp.route("/update-db/<string:title>/<string:form_type>", methods=['GET', 'POST'])
@admin_required
def update(title, form_type):
    # Initialize the appropriate form based on form_type
    if form_type == 'user':
        form = UserForm()
    elif form_type == 'dress':
        form = DressForm()
    elif form_type == 'rent':
        form = RentForm()
    else:
        flash('Invalid form type.', 'danger')
        return redirect(url_for('admin.inventory'))

    if form.validate_on_submit():
        if form_type == 'user':
            user = User(
                email=form.email.data,
                name=form.name.data,
                lastName=form.lastName.data,
                phoneNumber=form.phoneNumber.data
            )
            db.session.add(user)
            db.session.commit()
            flash('User added successfully into the database.')
            return redirect(url_for('admin.userInventory'))
        
        elif form_type == 'dress':
            dress = Dress(
                brand=form.brand.data,
                size=form.size.data,
                color=form.color.data,
                style=form.style.data,
                dressCost=form.dressCost.data,
                marketPrice=form.marketPrice.data,
                rentPrice=form.rentPrice.data,
            )
            db.session.add(dress)
            db.session.commit()
            flash('Dress added successfully into the database.')
            return redirect(url_for('admin.inventory'))
        
        elif form_type == 'rent':
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
                flash('Rent added successfully into the database.')
                return redirect(url_for('admin.rentInventory'))
            else:
                flash('Dress not available.')

    return render_template('admin_views/update.html', title=title, form_type=form_type, form=form)



@adminBp.route('/delete/<string:dataBase>/<int:id>', methods=['POST'])
@admin_required
def delete_object(dataBase, id):

    if dataBase == 'Dress':
        dress = Dress.query.get(int(id))

        if dress and not dress.rentStatus and not dress.maintenanceStatus:
            db.session.delete(dress)
            db.session.commit()
            flash('Dress deleted successfully.', 'success')
        else:
            flash('Dress not available.', 'danger')
    
        return redirect(url_for('admin.inventory'))

    
    elif dataBase == 'Rent':
        rent = Rent.query.get(int(id))

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
                # Handle unexpected errors that might occur during the process
                flash(f'Error: {str(e)}', 'danger')
                
            flash('Rent deleted successfully.', 'success')
            return redirect(url_for('admin.rentInventory'))
        else:
            flash('Rent not found.', 'danger')
    
    elif dataBase == 'User':
        user = User.query.get(int(id))

        if user and not user.check_status():
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully.', 'success')
            return redirect(url_for('admin.userInventory'))
        else:
            flash('User not found, or busy.', 'danger')



@adminBp.route('/download/excel')
@admin_required
def downloadExcell():

    from cordelia.excel import excel_download

    return excel_download()