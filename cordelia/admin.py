from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy import case, desc, func
from cordelia.auth import login_required, admin_required
from cordelia.db import db
from cordelia.models import Dress, Customer, Rent, Maintenance, maintenance_association
from cordelia.forms import SearchForm, DressForm, RentForm, CustomerForm, MaintenanceForm, DeleteForm
from base64 import b64encode

import logging


adminBp = Blueprint('admin', __name__, url_prefix='/admin')



@adminBp.route('/download/excel')
@login_required
@admin_required
def downloadExcel():

    from cordelia.excel import excel_download

    return excel_download()



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
    
    model_columns = Dress.__table__.columns.keys()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    # Get the selected column for ordering from the query parameters
    order_by_column = request.args.get('order_by', default='default')

    # Initial inventory query
    inventory_query = Dress.query

    # Apply sorting based on the selected column
    if order_by_column == 'times_rented':
        inventory_query = inventory_query.order_by(Dress.timesRented.desc())
    elif order_by_column == 'id':
        inventory_query = inventory_query.order_by(Dress.id)
    elif order_by_column == 'dress_cost':
        inventory_query = inventory_query.order_by(Dress.cost.desc())
    else:
        # If 'default', sort by rentStatus and maintenanceStatus in descending order.
        # Lastly by their last rent's rentDate and maintenance date if there is one.

        # Subquery to get the last rent date and the last maintenance date for each dress
        subquery = db.session.query(
            Rent.dressId,
            func.max(Rent.rentDate).label('last_rent_date'),
            func.max(Maintenance.date).label('last_maintenance_date')
        ).outerjoin(
            maintenance_association,
            Rent.dressId == maintenance_association.c.dress_id
        ).outerjoin(
            Maintenance,
            maintenance_association.c.maintenance_id == Maintenance.id
        ).group_by(Rent.dressId).subquery()

        # Query to order the Dress table
        inventory_query = Dress.query.outerjoin(
            subquery,
            Dress.id == subquery.c.dressId
        ).order_by(
            desc(Dress.rentStatus),
            desc(Dress.maintenanceStatus),
            desc(subquery.c.last_rent_date),
            desc(subquery.c.last_maintenance_date),
            desc(Dress.dateAdded)
        )

    # Handle search form
    inventory_query, form = handle_search_form(inventory_query, model_columns, Dress)

    # Paginate the filtered results and store it in 'inventory' variable
    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    # Separate pagination from the inventory query for pagination template to avoid errors.
    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    maintenance_form = MaintenanceForm()

    # Handle form submissions for the delete form
    if delete_form.validate_on_submit():
        dress_id = delete_form.id.data
        return redirect(url_for('admin.delete_object', dataBase='Dress', id=dress_id))
    
    # Handle form submissions for adding dresses to maintenance_form
    if maintenance_form.validate_on_submit():
        return redirect(url_for('admin.add_maintenance'))

    return render_template('admin_views/inventory_dress.html',
                           inventory=inventory,
                           form=form,
                           maintenance_form=maintenance_form,
                           delete_form=delete_form,
                           pagination=pagination,
                           order_by_column=order_by_column,
                           model=model)



@adminBp.route('/update-statuses', methods=['POST'])
@login_required
@admin_required
def update_statuses_endpoint():
    
    confirm = request.form.get('confirm', False)

    if confirm:
        Dress.update_statuses()
        db.session.commit()
        flash('Statuses updated successfully.', 'success')

    logging.debug("update_statuses() method called from dashboard")
    return redirect(url_for('admin.inventory'))



@adminBp.route('/maintenances', methods=['GET','POST'])
@login_required
def maintenance_inventory():
    model = 'Maintenance'

    model_columns = Maintenance.__table__.columns.keys()

    page = request.args.get('page', 1, type=int)
    items_per_page = 12

    order_by_column = request.args.get('order_by', default='default')

    inventory_query = Maintenance.query

    if order_by_column =='date':
        inventory_query = inventory_query.order_by(Maintenance.date.desc())
    elif order_by_column == 'type':
        inventory_query = inventory_query.order_by(Maintenance.maintenance_type.desc())
    elif order_by_column == 'cost':
        inventory_query = inventory_query.order_by(Maintenance.cost.desc())
    else:
        inventory_query = inventory_query.order_by(Maintenance.date.desc(), Maintenance.is_returned(Maintenance).desc())

    inventory_query, form = handle_search_form(inventory_query, model_columns, Maintenance)

    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    if delete_form.validate_on_submit():
        maintenance_id = delete_form.id.data
        return redirect(url_for('admin.delete_object', dataBase='Maintenance', id=maintenance_id))

    return render_template('admin_views/inventory_maintenance.html', 
                           inventory=inventory, 
                           form=form, 
                           delete_form=delete_form, 
                           pagination=pagination, 
                           order_by_column=order_by_column, 
                           model=model)



@adminBp.route('/set-maintenance', methods=['POST'])
@login_required
@admin_required
def add_maintenance():
    form = MaintenanceForm(request.form)

    selected_dresses = []
    for dress_id_form in form.dress_ids:
        dress_id = dress_id_form.dress_id.data
        if dress_id:
            dress = Dress.query.get(dress_id)
            if dress and not dress.check_status() and not dress.check_maintenance_status():
                selected_dresses.append(dress)
            else:
                flash('One or more dresses are unavaiable.', 'error')
                return redirect(url_for('admin.inventory'))

    date = form.maintenanceDate.data
    type = form.maintenanceType.data
    cost = form.maintenanceCost.data

    maintenance = Maintenance(
        date=date,
        maintenance_type=type,
        cost=cost,
        dresses=selected_dresses 
    )

    # Update maintenance status for selected dresses
    for dress in selected_dresses:
        if dress and not dress.rentStatus:
            dress.update_maintenance_status()

    db.session.add(maintenance)
    db.session.commit()
    flash('Maintenance record updated successfully!', 'success')
        
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
        inventory_query = inventory_query.join(Customer, Rent.clientId == Customer.id).order_by(Customer.lastName)
    elif order_by_column == 'dress_id':
        inventory_query = inventory_query.order_by(Rent.dressId.desc())
    else :
        inventory_query = inventory_query.order_by(Rent.rentDate.desc(),Rent.is_returned(Rent).desc())

    inventory_query, form = handle_search_form(inventory_query, model_columns, Rent)

    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    if delete_form.validate_on_submit():
        rent_id = delete_form.id.data
        return redirect(url_for('admin.delete_object', dataBase='Rent', id=rent_id))

    return render_template('admin_views/inventory_rent.html', 
                           inventory=inventory, 
                           form=form, 
                           delete_form=delete_form, 
                           pagination=pagination, 
                           order_by_column=order_by_column, 
                           model=model)



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
        inventory_query = inventory_query.order_by(Customer.lastName)
    elif order_by_column == 'date':
        inventory_query = inventory_query.order_by(Customer.dateAdded.desc())
    else :
        # Subquery to get the last rent date for each customer
        subquery = db.session.query(
            Rent.clientId,
            func.max(Rent.rentDate).label('last_rent_date')
        ).group_by(Rent.clientId).subquery()

        # Query to order the inventory_query
        inventory_query = inventory_query.outerjoin(
            subquery,
            Customer.id == subquery.c.clientId
        ).order_by(
            desc(case(
                (subquery.c.last_rent_date != None, subquery.c.last_rent_date),
                else_=None
            ))
        )

    inventory_query, form = handle_search_form(inventory_query, model_columns, Customer)

    inventory = inventory_query.paginate(page=page, per_page=items_per_page)

    pagination = inventory_query.paginate(page=page, per_page=items_per_page)

    delete_form = DeleteForm()

    if delete_form.validate_on_submit():
        customer_id = delete_form.id.data
        return redirect(url_for('admin.delete_object', dataBase='Customer', id=customer_id))

    return render_template('admin_views/inventory_customer.html', 
                           inventory=inventory, 
                           form=form, 
                           delete_form=delete_form, 
                           pagination=pagination, 
                           order_by_column=order_by_column, 
                           model=model)



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
                cost=form.cost.data,
                marketPrice=form.marketPrice.data,
                rentPrice=form.rentPrice.data,
                imageData=image_base64
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

            if not dress.check_status() and not dress.check_maintenance_status():
                rent = Rent(
                    dressId=form.dressId.data,
                    clientId=form.customerId.data,
                    rentDate=form.rentDate.data
                )
                
                db.session.add(rent)
                
                # Get id from un-committed rent for debugging purposes (cannot retrieve rent.id before commit).
                provisional_id = Rent.query.order_by(Rent.id.desc()).first()
                logging.debug(f'Rent {provisional_id} added but not yet committed')

                # Update associated dress
                dress.update_times_rented()
                dress.update_rent_status()
                logging.debug(f"{dress} update_times_rented() method called by created rent {provisional_id}")
                logging.debug(f"{dress} update_rent_status() method called by created rent {provisional_id}")

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

        if dress and not dress.check_status() and not dress.check_maintenance_status():
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
            # Store dress ID and customer ID before deleting rent object
            dress_id = rent.dressId

            db.session.delete(rent)

            associated_dress = Dress.query.get(dress_id)

            if associated_dress:
                associated_dress.update_times_rented()
                associated_dress.update_rent_status()
                
                logging.debug(f"update_times_rented() method called for {associated_dress}. After {rent} deletion.")
                logging.debug(f"update_rent_status() method called for {associated_dress}. After {rent} deletion.")
            else:
                flash(f'{associated_dress} not found.', 'danger')

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

    elif dataBase == 'Maintenance':
        maintenance = Maintenance.query.get(int(id))

        if maintenance and maintenance.is_returned():
            dresses = maintenance.dresses

            db.session.delete(maintenance)

            associated_dresses = Dress.query.filter(Dress.id.in_([dress.id for dress in dresses])).all()

            if associated_dresses:
                for dress in associated_dresses:
                    dress.update_maintenance_status()

            db.session.commit()

            flash(f'{maintenance} deleted successfully.', 'success')
            logging.debug(f"{maintenance} deleted from dashboard")

            return redirect(url_for('admin.maintenance_inventory'))
        else:
            flash("Cannot delete this maintenance.", 'danger')