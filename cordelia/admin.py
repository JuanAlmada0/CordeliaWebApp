from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import current_user
from cordelia.auth import login_required
from cordelia.db import db
from cordelia.models import Dress, Rent, Customer
from cordelia.forms import SearchForm, DressForm, RentForm, CustomerForm, MaintenanceForm, DeleteForm
from functools import wraps
import json
from datetime import datetime
from base64 import b64encode

import logging


adminBp = Blueprint('admin', __name__, url_prefix='/admin')


# (admin_required) wrapper
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.isAdmin:
            flash('This page requires Admin Access', 'message')
            # Store the current URL in the session
            session['next_page'] = request.url
            return redirect(url_for('auth.login'))
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
@login_required
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

    # Separate pagination query from the inventory query for pagination template to avoid errors.
    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    # Initialize delete and maintenance forms
    delete_form = DeleteForm()

    maintenance_form = MaintenanceForm()

    # Handle form submissions for the delete form
    if delete_form.validate_on_submit():
        dress_id = delete_form.id.data
        return redirect(url_for('admin.delete_object', dataBase='Dress', id=dress_id))

    # Handle form submissions for the maintenance form
    if maintenance_form.validate_on_submit():
        dress_id = maintenance_form.dress_id.data
        return redirect(url_for('admin.update_maintenance', dress_id=dress_id))

    return render_template('admin_views/inventory_dress.html', inventory=inventory, form=form, maintenance_form=maintenance_form, delete_form=delete_form, pagination=pagination, order_by_column=order_by_column, model=model)


@adminBp.route('/update-rent-statuses', methods=['POST'])
@login_required
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
@login_required
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

        # If a cost was submitted convert cost to integer
        maintenance_cost = int(maintenance_cost) if maintenance_cost else None
       
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
@login_required
@admin_required
def update_maintenance_status(dress_id):
    confirm = request.form.get('confirm', False)

    if confirm:
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
        inventory_query = inventory_query.order_by(Rent.id.desc())
    elif order_by_column == 'user_lastName':
        # Join Rent and Customer tables and sort by Customer's lastName
        inventory_query = inventory_query.join(Customer, Rent.clientId == Customer.id).order_by(Customer.lastName.desc())
    elif order_by_column == 'dress_id':
        inventory_query = inventory_query.order_by(Rent.dressId.desc())
    else :
        inventory_query = inventory_query.order_by(Rent.rentDate.desc())

    inventory_query, form = handle_search_form(inventory_query, model_columns, Rent)

    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    if delete_form.validate_on_submit():
        rent_id = delete_form.id.data
        return redirect(url_for('admin.delete_object', dataBase='Rent', id=rent_id))

    return render_template('admin_views/inventory_rent.html', inventory=inventory, form=form, delete_form=delete_form, pagination=pagination, order_by_column=order_by_column, model=model)


@adminBp.route('/customer-inventory', methods=["GET", "POST"])
@login_required
def customerInventory():
    model = 'Customer'

    model_columns = Customer.__table__.columns.keys()

    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    order_by_column = request.args.get('order_by', default='default')

    inventory_query = Customer.query

    if order_by_column == 'id':
        inventory_query = inventory_query.order_by(Customer.id)
    elif order_by_column == 'last_name':
        inventory_query = inventory_query.order_by(Customer.lastName.desc())
    elif order_by_column == 'date':
        inventory_query = inventory_query.order_by(Customer.dateAdded.desc())
    else :
        # 'order_by' Rent status with and an outer join with the Rent table to include all customers, even if they have no related rents.
        inventory_query = inventory_query.outerjoin(Rent).group_by(Customer.id).order_by(Rent.returnDate.desc(), Rent.is_returned(Rent).desc())

    inventory_query, form = handle_search_form(inventory_query, model_columns, Customer)

    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    if delete_form.validate_on_submit():
        customer_id = delete_form.id.data
        return redirect(url_for('admin.delete_object', dataBase='Customer', id=customer_id))

    return render_template('admin_views/inventory_customer.html', inventory=inventory, form=form, delete_form=delete_form, pagination=pagination, order_by_column=order_by_column, model=model)


@adminBp.route("/update-db/<string:title>/<string:form_type>", methods=['GET', 'POST'])
@login_required
def update(title, form_type):
    # Initialize form based on form_type
    if form_type == 'customer':
        form = CustomerForm()
    elif form_type == 'dress':
        form = DressForm()
    elif form_type == 'rent':
        form = RentForm()
    else:
        flash('Invalid form type.', 'danger')
        return redirect(url_for('admin.inventory'))

    if form.validate_on_submit():

        if form_type == 'customer':
            customer = Customer(
                email=form.email.data,
                name=form.name.data,
                lastName=form.lastName.data,
                phoneNumber=form.phoneNumber.data,
            )

            db.session.add(customer)
            db.session.commit()
            flash(f'{customer} added successfully into the database.')
            logging.debug(f"{customer} Added from dashboard")
            
            return redirect(url_for('admin.customerInventory'))

        if form_type == 'dress':
            # Get the image data from the request
            image_data = request.files.get('image')
            logging.debug(f'image_data from request: {image_data}')

            if image_data:
                # If the image_data is a file object, read it as bytes and convert to base64
                image_bytes = image_data.read()
                image_base64 = b64encode(image_bytes).decode('utf-8')
            else:
                # If the image_data is None, set image_base64 to None
                image_base64 = None

            dress = Dress(
                brand=form.brand.data,
                size=form.size.data,
                color=form.color.data,
                style=form.style.data,
                dressCost=form.dressCost.data,
                marketPrice=form.marketPrice.data,
                rentPrice=form.rentPrice.data,
                imageData=image_base64  # Store the image data in the database as base64 string or None
            )

            db.session.add(dress)
            db.session.commit()
            flash(f'{dress} added successfully into the database.')
            logging.debug(f"{dress} Added from dashboard")
            
            return redirect(url_for('admin.inventory'))
        
        elif form_type == 'rent':
            dress_id = form.dressId.data
            customer_id = form.customerId.data

            dress = Dress.query.get(dress_id)
            customer = Customer.query.get(customer_id)

            if not dress.rentStatus and not dress.maintenanceStatus:
                rent = Rent(
                    dressId=form.dressId.data,
                    clientId=form.customerId.data,
                    rentDate=form.rentDate.data
                )
                
                db.session.add(rent)
                
                # Get id from un-committed rent
                provisional_id = Rent.query.order_by(Rent.id.desc()).first()
                logging.debug(f'Rent {provisional_id} added but not yet committed')

                # Convert the provisional ID to a regular integer
                rent_id = provisional_id.id if provisional_id else None

                # Increment timesRented for dress object
                dress.update_times_rented()
                logging.debug(f"{dress} update_times_rented() method called by created rent {provisional_id}")

                # Update rentStatus for dress object
                dress.update_rent_status()
                logging.debug(f"{dress} update_rent_status() method called by created rent {provisional_id}")

                # Add rent log to the dress object
                dress_log = {
                    "date": form.rentDate.data.strftime('%Y-%m-%d'),
                    "id": rent_id,
                    "customer_id": [customer.id, customer.lastName, customer.name]
                }
                dress.update_rent_log(dress_log)
                logging.debug(f"{dress} rent log updated by rent {provisional_id}")

                # Add rent log to the customer object
                customer_log = {
                    "date": form.rentDate.data.strftime('%Y-%m-%d'),
                    "id": rent_id,
                    "dress_id": dress.id
                }
                customer.update_rent_log(customer_log)
                logging.debug(f"{customer} rent log updated by rent {provisional_id}")

                # Create log for rent
                rent_log = {
                    "date": form.rentDate.data.strftime('%Y-%m-%d'),
                    "customer_id": customer_id,
                    "dress_id": dress_id
                } 
                rent.update_rent_log(rent_log)
                logging.debug(f"rent {provisional_id} rent log updated by itself.")

                # Commit rent object
                db.session.commit()
                logging.debug(f"{rent} committed")
                flash(f'{rent} added successfully into the database.')
                logging.debug(f"{rent} Added from dashboard")

                return redirect(url_for('admin.rentInventory'))
            else:
                flash('Dress not available.')

    return render_template('admin_views/update.html', title=title, form_type=form_type, form=form)


@adminBp.route('/delete/<string:dataBase>/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_object(dataBase, id):

    if dataBase == 'Dress':
        dress = Dress.query.get(int(id))

        if dress and not dress.rentStatus and not dress.maintenanceStatus:
            db.session.delete(dress)
            db.session.commit()
            flash(f'{dress} deleted successfully.', 'success')
            logging.debug(f"{dress} deleted from dashboard")
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
                associated_dress.update_times_rented()
                associated_dress.update_rent_status()
                logging.debug(f"update_rent_status() method called for {associated_dress}. After {rent} deletion.")
                logging.debug(f"update_times_rented() method called for {associated_dress}. After {rent} deletion.")
            else:
                # Handle the case when the associated dress is not found
                flash(f'{associated_dress} not found when trying to decrement times_rented.', 'danger')

            db.session.commit()
            flash(f'{rent} deleted successfully.', 'success')
            logging.debug(f"{rent} deleted from dashboard")
            return redirect(url_for('admin.rentInventory'))
        else:
            flash('Rent not found.', 'danger')
    
    elif dataBase == 'Customer':
        customer = Customer.query.get(int(id))

        if customer and not customer.check_status():
            db.session.delete(customer)
            db.session.commit()
            flash(f'{customer} deleted successfully.', 'success')
            logging.debug(f"{customer} deleted from dashboard")
            return redirect(url_for('admin.customerInventory'))
        else:
            flash("Can't delete this customer.", 'danger')


@adminBp.route('/download/excel')
@login_required
def downloadExcel():

    from cordelia.excel import excel_download

    return excel_download()


@adminBp.route('/upload/excel')
@login_required
def uploadExcel():

    from cordelia.excel import excel_upload

    return excel_upload()