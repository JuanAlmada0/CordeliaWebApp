from flask import current_app, send_file
import pandas as pd
import os
from datetime import datetime
from cordelia.db import db
from cordelia.models import Dress, Rent, User


def excel_download():
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
        'Rent Status': [dress.rentStatus for dress in dresses],
        'Maintenance Status' : [dress.maintenanceStatus for dress in dresses]
    }
    user_data = {
        'User Id': [user.id for user in users],
        'Username': [user.username if user.username else 'None' for user in users],
        'Email': [user.email for user in users],
        'Name': [user.name for user in users],
        'Last Name': [user.lastName for user in users],
        'Phone Number': [str(user.phoneNumber) for user in users],
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

    current_datetime = datetime.now().strftime('%B-%d-%Y_%H-%M-%S')

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