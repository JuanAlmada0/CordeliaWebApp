from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from cordelia.auth import login_required
from cordelia.db import db
from cordelia.models import Dress, Rent, User
from cordelia.forms import SearchForm, DressForm, RentForm, UserForm, MaintenanceForm, DeleteForm
from functools import wraps
import json
from datetime import datetime

import logging


adminBp = Blueprint('admin', __name__, url_prefix='/admin')



# (admin_required) wrapper
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if not current_user.isAdmin:
        if not current_user:
            flash('This page requires Admin Access', 'message')
            return redirect(url_for('home.home'))
        return f(*args, **kwargs)
    return decorated_function



# SearchForm handler
def handle_search_form(query, model_columns, model_class):
    form = SearchForm(model_columns=model_columns)

    if form.validate_on_submit():
        category = form.category.data
        filterSearch = form.search.data

        model_columns = {column: getattr(model_class, column) for column in model_columns}

        if category and filterSearch and category in model_columns:
            column = model_columns[category]
            query = query.filter(column.ilike(f"%{filterSearch}%"))

    return query, form



@adminBp.route('/inventory', methods=['GET', 'POST'])
#@login_required
def inventory():
    model = 'Dress'
    # Get the list of model columns for the Dress table
    model_columns = Dress.__table__.columns.keys()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    # Get the selected column for ordering from the query parameters
    order_by_column = request.args.get('order_by', default='default')

    # Get the initial inventory query
    inventory_query = Dress.query

    # Apply sorting based on the selected column
    if order_by_column == 'times_rented':
        inventory_query = inventory_query.order_by(Dress.timesRented.desc())
    elif order_by_column == 'id':
        inventory_query = inventory_query.order_by(Dress.id)
    elif order_by_column == 'dress_cost':
        inventory_query = inventory_query.order_by(Dress.dressCost.desc())
    else :
        # If 'default', sort by rentStatus and maintenanceStatus in descending order
        inventory_query = inventory_query.order_by(Dress.rentStatus.desc(), Dress.maintenanceStatus.desc())

    # Handle search form
    inventory_query, form = handle_search_form(inventory_query, model_columns, Dress)

    # Paginate the filtered results and store it in 'inventory' variable
    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    # Separate pagination query from the inventory query for pagination template
    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    # Initialize delete and maintenance forms
    delete_form = DeleteForm()

    maintenance_form = MaintenanceForm()

    # Handle form submissions for the delete form
    if delete_form.validate_on_submit():
        dress_id = delete_form.dress_id.data
        return redirect(url_for('admin.delete_object', dataBase='Dress', id=dress_id))

    # Handle form submissions for the maintenance form
    if maintenance_form.validate_on_submit():
        dress_id = maintenance_form.dress_id.data
        return redirect(url_for('admin.update_maintenance', dress_id=dress_id))

    return render_template('admin_views/inventory.html', inventory=inventory, form=form, maintenance_form=maintenance_form, delete_form=delete_form, pagination=pagination, order_by_column=order_by_column, model=model)



@adminBp.route('/update-rent-statuses', methods=['POST'])
@admin_required
def update_rent_statuses_endpoint():
    
    confirm = request.form.get('confirm', False)

    if confirm:
        Dress.update_rent_statuses()
        db.session.commit()
        flash('Rent statuses updated successfully.', 'success')

    logging.debug("update_rent_statuses() method called from dashboard")
    return redirect(url_for('admin.inventory'))


# Handles modal for maintenance form on the dress inventory dashboard
@adminBp.route('/update-dress/<int:dress_id>', methods=['POST'])
@admin_required
def update_maintenance(dress_id):
    dress = Dress.query.get(int(dress_id))

    if dress and not dress.rentStatus:
        # Update maintenance status
        dress.toggle_maintenance_status()
        
        # Get the maintenance data from the form
        maintenance_date = request.form.get("maintenanceDate")
        maintenance_type = request.form.get("maintenanceType")
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
            "type": maintenance_type,
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
        dress.toggle_maintenance_status()
        db.session.commit()
        flash("Maintenance status updated successfully!", 'success')
    else:
        flash("Dress not found!", 'error')

    return redirect(url_for('admin.inventory'))



@adminBp.route('/rent-inventory', methods=['GET', 'POST'])
@login_required
def rentInventory():
    model = 'Rent'

    model_columns = Rent.__table__.columns.keys()

    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    order_by_column = request.args.get('order_by', default='default')

    inventory_query = Rent.query

    if order_by_column == 'id':
        inventory_query = inventory_query.order_by(Rent.id)
    elif order_by_column == 'user_id':
        inventory_query = inventory_query.order_by(Rent.clientId.desc())
    elif order_by_column == 'dress_id':
        inventory_query = inventory_query.order_by(Rent.dressId.desc())
    else :
        inventory_query = inventory_query.order_by(Rent.rentDate.desc())

    inventory_query, form = handle_search_form(inventory_query, model_columns, Rent)

    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    if delete_form.validate_on_submit():
        rent_id = delete_form.rent_id.data
        return redirect(url_for('admin.delete_object', dataBase='Rent', id=rent_id))

    return render_template('admin_views/rentInventory.html', inventory=inventory, form=form, delete_form=delete_form, pagination=pagination, order_by_column=order_by_column, model=model)


@adminBp.route('/user-inventory', methods=["GET", "POST"])
@login_required
def userInventory():
    model = 'User'

    model_columns = User.__table__.columns.keys()

    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    order_by_column = request.args.get('order_by', default='default')

    inventory_query = User.query

    if order_by_column == 'name':
        inventory_query = inventory_query.order_by(User.name)
    elif order_by_column == 'last_name':
        inventory_query = inventory_query.order_by(User.lastName)
    elif order_by_column == 'date':
        inventory_query = inventory_query.order_by(User.joinedAtDate.desc())
    else :
        inventory_query = inventory_query.order_by(User.id)

    inventory_query, form = handle_search_form(inventory_query, model_columns, User)

    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    if delete_form.validate_on_submit():
        user_id = delete_form.user_id.data
        return redirect(url_for('admin.delete_object', dataBase='User', id=user_id))

    return render_template('admin_views/userInventory.html', inventory=inventory, form=form, delete_form=delete_form, pagination=pagination, order_by_column=order_by_column, model=model)



@adminBp.route("/update-db/<string:title>/<string:form_type>", methods=['GET', 'POST'])
@login_required
def update(title, form_type):
    # Initialize form based on form_type
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
            if current_user.isAdmin:
                user = User(
                    email=form.email.data,
                    name=form.name.data,
                    lastName=form.lastName.data,
                    phoneNumber=form.phoneNumber.data,
                )

                db.session.add(user)
                db.session.commit()
                flash(f'{user} added successfully into the database.')
                logging.debug(f"{user} Added on dashboard")
                
                return redirect(url_for('admin.userInventory'))
            else:
                redirect(url_for('admin.userInventory'))
        
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
            flash(f'{dress} added successfully into the database.')
            logging.debug(f"{dress} Added on dashboard")

            return redirect(url_for('admin.inventory'))
        
        elif form_type == 'rent':
            dress_id = form.dressId.data
            user_id = form.userId.data

            dress = Dress.query.get(dress_id)
            user = User.query.get(user_id)

            if not dress.rentStatus and not dress.maintenanceStatus:
                rent = Rent(
                    dressId=form.dressId.data,
                    clientId=form.userId.data,
                    rentDate=form.rentDate.data
                )
                
                db.session.add(rent)
                
                # Get id from un-committed rent
                provisional_id = Rent.query.order_by(Rent.id.desc()).first()
                logging.debug(f'Rent {provisional_id} added but not yet committed')

                # Convert the provisional ID to a regular integer
                rent_id = provisional_id.id if provisional_id else None

                # Increment timesRented for dress object
                dress.increment_times_rented()
                logging.debug(f"{dress} increment_times_rented() method called by created rent {provisional_id}")

                # Update rentStatus for dress object
                current_date = datetime.utcnow().date()
                if rent.returnDate >= current_date:
                    dress.toggle_rent_status()
                    logging.debug(f"{dress} toggle_rent_status() method called by created rent {provisional_id}")

                # Add rent log to the dress object
                dress_log = {
                    "date": form.rentDate.data.strftime('%Y-%m-%d'),
                    "id": rent_id,
                    "user_id": [user.id, user.lastName, user.name]
                }
                dress.update_rent_log(dress_log)
                logging.debug(f"{dress} rent log updated by rent {provisional_id}")

                # Add rent log to the user object
                user_log = {
                    "date": form.rentDate.data.strftime('%Y-%m-%d'),
                    "id": rent_id,
                    "dress_id": dress.id
                }

                user.update_rent_log(user_log)
                logging.debug(f"{user} rent log updated by rent {provisional_id}")

                # Commit rent object
                db.session.commit()
                logging.debug(f"{rent} committed")
                flash(f'{rent} added successfully into the database.')
                logging.debug(f"{rent} Added on dashboard")

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
            logging.debug("Dress deleted from dashboard")
        else:
            flash('Dress not available.', 'danger')
    
        return redirect(url_for('admin.inventory'))
    
    elif dataBase == 'Rent':
        rent = Rent.query.get(int(id))

        if rent and rent.is_returned():
            # Store dress ID before deleting rent object
            dress_id = rent.dressId
            db.session.delete(rent)
            # Attempt to find the associated dress and decrement times_rented
            associated_dress = Dress.query.get(dress_id)
            if associated_dress:
                associated_dress.decrement_times_rented()
                logging.debug(f"'decrement_rent_status()' method called for Associated Dress. After {rent} deletion.")
            else:
                # Handle the case when the associated dress is not found
                flash('Associated Dress not found when trying to decrement times_rented.', 'danger')

            db.session.commit()
            flash('Rent deleted successfully.', 'success')
            logging.debug("Rent deleted from dashboard")
            return redirect(url_for('admin.rentInventory'))
        else:
            flash('Rent not found.', 'danger')
    
    elif dataBase == 'User':
        user = User.query.get(int(id))

        if user and not user.check_status() and not user.isAdmin:
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully.', 'success')
            logging.debug("User deleted from dashboard")
            return redirect(url_for('admin.userInventory'))
        else:
            flash("Can't delete this user.", 'danger')



@adminBp.route('/download/excel')
@login_required
def downloadExcell():

    from cordelia.excel import excel_download

    return excel_download()