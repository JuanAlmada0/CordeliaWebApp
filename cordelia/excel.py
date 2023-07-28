from flask import current_app, send_file
import pandas as pd
import json
import os
from datetime import datetime
from cordelia.models import Dress, Rent, Customer


def excel_download():
    
    dresses = Dress.query.all()
    customers = Customer.query.all()
    rents = Rent.query.all()

    if dresses:
        
        dress_data = {
            'Dress Id': [dress.id for dress in dresses],
            'Size': [dress.size for dress in dresses],
            'Color': [dress.color for dress in dresses],
            'Style': [dress.style for dress in dresses],
            'Brand': [dress.brand for dress in dresses],
            'Dress Cost': [dress.dressCost for dress in dresses],
            'Market Price': [dress.marketPrice for dress in dresses],
            'Rent Price': [dress.rentPrice for dress in dresses],
            'Rents for Returns': [dress.rentsForReturns for dress in dresses],
            'Times Rented': [dress.timesRented for dress in dresses],
            'Sellable': [dress.sellable for dress in dresses],
            'Rent Status': [dress.rentStatus for dress in dresses],
            'Maintenance Status': [dress.maintenanceStatus for dress in dresses],
            'Maintenance Log': [json.loads(dress.rentLog) if dress.rentLog else None for dress in dresses],
            'Rent Log': [json.loads(dress.rentLog) if dress.rentLog else None for dress in dresses]
        }

        df_dress = pd.DataFrame(dress_data)
        
    if customers:

        customer_data = {
            'User Id': [customer.id if customer.id else None for customer in customers],
            'Email': [customer.email for customer in customers],
            'Name': [customer.name for customer in customers],
            'Last Name': [customer.lastName for customer in customers],
            'Phone Number': [str(customer.phoneNumber) for customer in customers],
            'Date Added': [customer.dateAdded.strftime('%Y-%m-%d') for customer in customers],
            'Rent Log': [json.loads(customer.rentLog) if customer.rentLog else None for customer in customers]
        }

        df_customer = pd.DataFrame(customer_data)

    if rents:

        rent_data = {
            'Rent Id': [rent.id for rent in rents],
            'Dress Id': [rent.dressId for rent in rents],
            'User Id': [rent.clientId for rent in rents],
            'Rent Date': [rent.rentDate.strftime('%Y-%m-%d') for rent in rents],
            'Return Date': [rent.returnDate.strftime('%Y-%m-%d') if rent.returnDate else '' for rent in rents],
            'Payment Total': [rent.paymentTotal for rent in rents],
            'Rent Log': [json.loads(rent.rentLog) if rent.rentLog else None for rent in rents]
        }

        df_rent = pd.DataFrame(rent_data)
    
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

    # Return the file as an attachment
    return send_file(
        file_path,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
