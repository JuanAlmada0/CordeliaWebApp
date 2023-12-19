from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from ..models import Dress  
import logging

api_dress_bp = Blueprint('api_dress', __name__, url_prefix='/api/dresses')


def dress_model_to_dict(dresses):
    dress_list = []

    for dress in dresses:
        dress_info = {
            'id': dress.id,
            'size': dress.size,
            'color': dress.color,
            'style': dress.style,
            'brand': dress.brand,
            'cost': dress.cost,
            'marketPrice': dress.marketPrice,
            'rentPrice': dress.rentPrice,
            'rentsForReturns': dress.rentsForReturns,
            'sellable': dress.sellable,
            'dateAdded': dress.dateAdded.isoformat(),
            'timesRented': dress.timesRented,
            'rentStatus': dress.rentStatus,
            'maintenanceStatus': dress.maintenanceStatus,
            'sold': dress.sold
        }
        dress_list.append(dress_info)
    return dress_list


def additional_filters(query, *filters):
    for filter_condition in filters:
        query = query.filter(filter_condition)
    
    dresses = query.all()
    return dress_model_to_dict(dresses)


@api_dress_bp.route('/all', methods=['GET'])
def get_all_dresses():
    dresses = Dress.query.all()
    dress_list = dress_model_to_dict(dresses)
    if not dress_list:
            return jsonify({'message': 'No dresses found.'})
    return jsonify({'dresses': dress_list})


@api_dress_bp.route('/<int:dress_id>', methods=['GET'])
def get_dress_by_id(dress_id):
    try:
        dress = Dress.query.get_or_404(dress_id)
        dress_info = dress_model_to_dict([dress])[0]
        return jsonify(dress_info)
    except HTTPException as e:
        # Handle the exception
        if e.code == 404:
            # Dress not found
            return jsonify({'error': 'Dress not found'}), 404
        else:
            # Other HTTP exceptions
            return jsonify({'error': 'An unexpected error occurred'}), 500


@api_dress_bp.route('/search', methods=['GET'])
def search_dresses():
    try:
        # Example: /api/dresses/search?size=9&color=blue&brand=Valentino&min_cost=800&max_cost=3000
        color = request.args.get('color', type=str)
        brand = request.args.get('brand', type=str)
        size = request.args.get('size', type=int)
        style = request.args.get('style', type=str)

        # Additional search parameters
        min_cost = request.args.get('min_cost', type=int)
        max_cost = request.args.get('max_cost', type=int)

        logging.debug(f'min_cost arg: {min_cost}, max_cost arg: {max_cost}')

        query = Dress.query

        if color:
            # Use ilike for case-insensitive color search
            query = query.filter(func.lower(Dress.color).ilike(f"%{color.lower()}%"))
        if brand:
            query = query.filter_by(brand=brand)
        if size:
            query = query.filter_by(size=size)
        if style:
            query = query.filter_by(style=style)
        
        logging.debug(f'color: {color}, brand: {brand}, size: {size}, style: {style}, min_cost: {min_cost}, max_cost: {max_cost}')

        # Apply additional filters based on cost range
        filters = []
        if min_cost:
            filters.append(Dress.cost >= min_cost)
        if max_cost:
            filters.append(Dress.cost <= max_cost)


        logging.debug(f'Filter values: {", ".join(str(f) for f in filters)}')

        dress_list = additional_filters(query, *filters)

        if not dress_list:
            return jsonify({'message': 'No dresses found matching the search criteria.'})

        return jsonify({'dresses': dress_list})
    
    except SQLAlchemyError as e:
        logging.error(f'SQLAlchemy error: {str(e)}')
        return jsonify({'error': 'A database error occurred.'}), 500
    except TypeError as e:
        logging.error(f'Type error: {str(e)}')
        return jsonify({'error': 'Invalid data type.'}), 400
    except Exception as e:
        logging.error(f'An unexpected error occurred: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred.'}), 500
    