from flask import current_app, send_file, request, jsonify
import pandas as pd
import json
import os
from datetime import datetime
from cordelia.models import Dress, Rent, Customer, Maintenance
from cordelia.db import db



def excel_download():
    
    dresses = Dress.query.all()
    customers = Customer.query.all()
    rents = Rent.query.all()
    maintenances = Maintenance.query.all()

    if dresses:
        
        dress_data = {
            'Id': [dress.id for dress in dresses],
            'Size': [dress.size for dress in dresses],
            'Color': [dress.color for dress in dresses],
            'Style': [dress.style for dress in dresses],
            'Brand': [dress.brand for dress in dresses],
            'Cost': [dress.cost for dress in dresses],
            'Date Added': [dress.dateAdded.strftime('%Y-%m-%d') for dress in dresses],
            'Market Price': [dress.marketPrice for dress in dresses],
            'Rent Price': [dress.rentPrice for dress in dresses],
            'Rents for Returns': [dress.rentsForReturns for dress in dresses],
            'Times Rented': [dress.timesRented for dress in dresses],
            'Sellable': [dress.sellable for dress in dresses],
            'Rent Status': [dress.rentStatus for dress in dresses],
            'Maintenance Status': [dress.maintenanceStatus for dress in dresses]
        }

        df_dress = pd.DataFrame(dress_data)
        
    if customers:

        customer_data = {
            'Id': [customer.id if customer.id else None for customer in customers],
            'Email': [customer.email for customer in customers],
            'Name': [customer.name for customer in customers],
            'Last Name': [customer.lastName for customer in customers],
            'Phone Number': [str(customer.phoneNumber) for customer in customers],
            'Date Added': [customer.dateAdded.strftime('%Y-%m-%d') for customer in customers]
        }

        df_customer = pd.DataFrame(customer_data)

    if rents:

        rent_data = {
            'Id': [rent.id for rent in rents],
            'Dress Id': [rent.dressId for rent in rents],
            'Customer Id': [rent.clientId for rent in rents],
            'Rent Date': [rent.rentDate.strftime('%Y-%m-%d') for rent in rents],
            'Return Date': [rent.returnDate.strftime('%Y-%m-%d') if rent.returnDate else '' for rent in rents],
            'Payment Total': [rent.paymentTotal for rent in rents],
            'Payment Method': [rent.paymentMethod for rent in rents]
        }

        df_rent = pd.DataFrame(rent_data)

    if maintenances:

        maintenance_data = {
            'Id': [maintenance.id for maintenance in maintenances],
            'Type': [maintenance.maintenance_type for maintenance in maintenances],
            'Date': [maintenance.date.strftime('%Y-%m-%d') for maintenance in maintenances],
            'Return Date': [maintenance.returnDate.strftime('%Y-%m-%d') if maintenance.returnDate else '' for maintenance in maintenances],
            'Total Cost': [maintenance.cost for maintenance in maintenances],
            'Dresses': [maintenance.dresses for maintenance in maintenances],
        }

        df_maintenance = pd.DataFrame(maintenance_data)

    
    instance_path = os.path.join(current_app.instance_path, 'uploads')
    os.makedirs(instance_path, exist_ok=True)

    current_datetime = datetime.now().strftime('%B-%d-%Y_%H-%M-%S')

    file_name = f'database_data_{current_datetime}.xlsx'

    file_path = os.path.join(current_app.instance_path, 'uploads', file_name)
    

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as excel_writer:
        if dresses:
            df_dress.to_excel(excel_writer, sheet_name='Dresses', index=False)
        if customers:
            df_customer.to_excel(excel_writer, sheet_name='Customers', index=False)
        if rents:
            df_rent.to_excel(excel_writer, sheet_name='Rents', index=False)
        if maintenances:
            df_maintenance.to_excel(excel_writer, sheet_name='Maintenances', index=False)

    # Return the file as an attachment
    return send_file(
        file_path,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



def excel_upload():

    # Check if the file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    # Check if a file is selected and it has a supported extension
    if file.filename == '' or not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Please select a valid XLSX file'}), 400
    
    try:
        df_dress = pd.read_excel(file, sheet_name='Dresses')
        df_rents = pd.read_excel(file, sheet_name='Rents')
        df_customers = pd.read_excel(file, sheet_name='Customers')
        # Convert column names to lowercase to ensure case-insensitivity
        df_dress.columns = df_dress.columns.str.lower()
        df_rents.columns = df_rents.columns.str.lower()
        df_customers.columns = df_customers.columns.str.lower()

        if df_dress:
            for index, row in df_dress.iterrows():
                dress_id = row['dress id'] 
                dress = Dress.query.get(dress_id)

                if dress:
                    dress.size = row['size']
                    dress.color = row['color']
                    dress.style = row['style']
                    dress.brand = row['brand']
                    dress.cost = row['cost']
                    dress.marketPrice = row['market price'] if row['market price'] else None
                    dress.rentPrice = row['rent price']
                else:
                    dress = Dress(
                        id = dress_id,
                        size = row['size'],
                        color = row['color'],
                        style = row['style'],
                        brand = row['brand'],
                        cost = row['cost'],
                        marketPrice = row['market price'] if row['market price'] else None,
                        rentPrice = row['rent price'],
                    )
                    db.session.add(dress)
        # Commit the changes to the database
        db.session.commit()

        return jsonify({'message': 'Database updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to update database. Error: ' + str(e)}), 500