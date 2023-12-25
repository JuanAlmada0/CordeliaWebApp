from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from ..models import Dress, Rent, Maintenance, Sale, maintenance_association


api_transactions_bp = Blueprint('api_transactions', __name__, url_prefix='/api/transactions')


def rent_model_to_dict(rents):
    rent_list = []

    for rent in rents:
        rent_info = {
            'id': rent.id,
            'dressId': rent.dressId,
            'clientId': rent.clientId,
            'rentDate': rent.rentDate.isoformat(),
            'returnDate': rent.returnDate.isoformat() if rent.returnDate else None,
            'paymentMethod': rent.paymentMethod,
            'paymentTotal': rent.paymentTotal,
            'isReturned': rent.is_returned(),
        }
        rent_list.append(rent_info)
    return rent_list


def maintenance_model_to_dict(maintenances):
    maintenance_list = []

    for maintenance in maintenances:
        dress_query = Dress.query.join(maintenance_association).filter(maintenance_association.c.maintenance_id == maintenance.id)
        dresses_info = [
            {
                'id': dress.id,
            }
            for dress in dress_query.all()
        ]

        maintenance_info = {
            'id': maintenance.id,
            'date': maintenance.date.isoformat(),
            'returnDate': maintenance.returnDate.isoformat(),
            'maintenanceType': maintenance.maintenance_type,
            'cost': maintenance.cost,
            'dresses': dresses_info,
        }
        maintenance_list.append(maintenance_info)
    return maintenance_list



def sale_model_to_dict(sales):
    sale_list = []

    for sale in sales:
        sale_info = {
            'id': sale.id,
            'saleDate': sale.sale_date.isoformat(),
            'salePrice': sale.sale_price,
            'customerId': sale.customer_id,
            'dressId': sale.dress_id,
        }
        sale_list.append(sale_info)
    return sale_list



@api_transactions_bp.route('/rents/all', methods=['GET'])
def get_all_rents():
    rents = Rent.query.all()
    rent_list = rent_model_to_dict(rents)
    if not rent_list:
            return jsonify({'message': 'No rents found.'})
    return jsonify({'rents': rent_list})



@api_transactions_bp.route('/maintenances/all', methods=['GET'])
def get_all_maintenances():
    maintenances = Maintenance.query.all()
    maintenance_list = maintenance_model_to_dict(maintenances)
    if not maintenance_list:
        return jsonify({'message': 'No maintenances found.'})
    return jsonify({'maintenances': maintenance_list})



@api_transactions_bp.route('/sales/all', methods=['GET'])
def get_all_sales():
    sales = Sale.query.all()
    sales_list = sale_model_to_dict(sales)
    if not sales_list:
        return jsonify({'message': 'No sales found.'})
    return jsonify({'sales': sales_list})



@api_transactions_bp.route('/rents/<int:rent_id>', methods=['GET'])
def get_rent_by_id(rent_id):
    try:
        rent = Rent.query.get_or_404(rent_id)
        rent_info = rent_model_to_dict([rent])[0]

        return jsonify(rent_info)
    
    except HTTPException as e:
        # Handle the exception (from get_or_404)
        if e.code == 404:
            return jsonify({'error': 'Rent not found'}), 404
        else:
            return jsonify({'error': 'An unexpected error occurred'}), 500



@api_transactions_bp.route('/maintenances/<int:maintenance_id>', methods=['GET'])
def get_maintenance_by_id(maintenance_id):
    try:
        maintenance = Maintenance.query.get_or_404(maintenance_id)
        maintenance_info = maintenance_model_to_dict([maintenance])[0]

        return jsonify(maintenance_info)
    
    except HTTPException as e:
        if e.code == 404:
            return jsonify({'error': 'Maintenance not found'}), 404
        else:
            return jsonify({'error': 'An unexpected error occurred'}), 500



@api_transactions_bp.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale_by_id(sale_id):
    try:
        sale = Sale.query.get_or_404(sale_id)
        sale_info = sale_model_to_dict([sale])[0]

        return jsonify(sale_info)
    
    except HTTPException as e:
        if e.code == 404:
            return jsonify({'error': 'Sale not found'}), 404
        else:
            return jsonify({'error': 'An unexpected error occurred'}), 500


