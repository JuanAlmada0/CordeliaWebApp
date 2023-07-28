from cordelia.db import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
import json

import logging


class Dress(db.Model):
    # Dress model representing a dress item in the database
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(20), index=True, nullable=False)
    color = db.Column(db.String(20), index=True, nullable=False)
    style = db.Column(db.String(20), index=True, nullable=False)
    brand = db.Column(db.String(20), index=True, nullable=False)
    dressCost = db.Column(db.Integer, index=True, nullable=False)
    marketPrice = db.Column(db.Integer, index=True, default=None)
    rentPrice = db.Column(db.Integer, index=True, nullable=False)
    rentsForReturns = db.Column(db.Integer, index=True)
    timesRented = db.Column(db.Integer, index=True, default=0)
    sellable = db.Column(db.Boolean, index=True, default=False)
    dateAdded = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    rentStatus = db.Column(db.Boolean, index=True, default=False)
    rentLog = db.Column(db.JSON, nullable=True, default=[])
    maintenanceStatus = db.Column(db.Boolean, index=True, default=False)
    maintenanceLog = db.Column(db.JSON, nullable=True, default=[])

    def __init__(self, *args, **kwargs):
        super(Dress, self).__init__(*args, **kwargs)

        self.rentsForReturns = self.dressCost // self.rentPrice

    def toggle_maintenance_status(self):
        self.maintenanceStatus = not self.maintenanceStatus

    def get_maintenance_log(self):
        log = []
        if self.maintenanceLog:
            # Parse the JSON data stored in 'maintenanceLog' into a Python list of dictionaries
            log = json.loads(self.maintenanceLog)
            # Sort the list of maintenance log dictionaries by the 'date' key in descending order
            log.sort(key=lambda x: x['date'], reverse=True)
            return log
    
    def update_rent_log(self, log):
        existing_rent_log = json.loads(self.rentLog) if self.rentLog else []
        existing_rent_log.append(log)
        # Save the updated rent log to the dress
        self.rentLog = json.dumps(existing_rent_log)

    def get_rent_log(self):
        log = []
        if self.rentLog:
            log = json.loads(self.rentLog)
            log.sort(key=lambda x: x['date'], reverse=True)
            return log
    
    def parse_date(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    
    def get_last_maintenance(self):
        if self.maintenanceLog:
            log = json.loads(self.maintenanceLog)
            latest_maintenance_str = max(log, key=lambda x: x['date'])['date']
            # Call the 'parse_date' method to convert the 'latest_maintenance_str' into a date object
            return self.parse_date(latest_maintenance_str)

    def get_last_rent(self):
        if self.rentLog:
            log = json.loads(self.rentLog)
            latest_rent_str = max(log, key=lambda x: x['date'])['date']
            return self.parse_date(latest_rent_str)

    def increment_times_rented(self):
        self.timesRented += 1
        self.sellable = self.timesRented > self.rentsForReturns

    def decrement_times_rented(self):
        self.timesRented -= 1
        self.sellable = self.timesRented > self.rentsForReturns
    
    def toggle_rent_status(self):
        self.rentStatus = not self.rentStatus

    def update_times_rented(self):
        associated_rents = Rent.query.filter_by(dressId=self.id).all()
        if associated_rents:
            num_of_rents = len(associated_rents)
            # Update the timesRented and sellable attributes
            self.timesRented = num_of_rents
            self.sellable = num_of_rents > self.rentsForReturns
        else:
            self.timesRented = 0
            self.sellable = self.timesRented > self.rentsForReturns

    def update_rent_status(self):
        # Latest rent associated with this dress
        associated_rent = Rent.query.filter_by(dressId=self.id).order_by(Rent.rentDate.desc()).first()
        if not associated_rent:
            self.rentStatus = False
        else:
            # Check if the latest rent has been returned
            self.rentStatus = not associated_rent.is_returned()

    @classmethod
    def update_rent_statuses(cls):
        dresses = cls.query.all()

        for dress in dresses:
            dress.update_rent_status()
            dress.update_times_rented()      
            
        logging.debug("update_rent_statuses() method executed.")
    
    def __repr__(self):
        return f"Dress D-0{self.id}"
    


class Customer(db.Model):
    # User model representing a user in the database
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), index=True, unique=True, nullable=True)
    name = db.Column(db.String(60), index=True)
    lastName = db.Column(db.String(60), index=True)
    phoneNumber = db.Column(db.Integer, index=True, unique=True, nullable=True)
    dateAdded = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    rentLog = db.Column(db.JSON, nullable=True, default=[])
    
    def check_status(self):
        associated_rent = Rent.query.filter_by(clientId=self.id).order_by(Rent.rentDate.desc()).first()
        # Check if there is any related rent
        if not associated_rent:
            return False
        else:
            # Check if the latest rent has been returned
            return not associated_rent.is_returned()
    
    def update_rent_log(self, log):
        existing_rent_log = json.loads(self.rentLog) if self.rentLog else []
        existing_rent_log.append(log)
        self.rentLog = json.dumps(existing_rent_log)
    
    def get_rent_log(self):
        log = []
        if self.rentLog:
            log = json.loads(self.rentLog)
            log.sort(key=lambda x: x['date'], reverse=True)
            return log
    
    def get_last_rent(self):
        if self.rentLog:
            log = json.loads(self.rentLog)
            latest_rent_str = max(log, key=lambda x: x['date'])['date']
            latest_rent = datetime.strptime(latest_rent_str, "%Y-%m-%d").date()
            return latest_rent
    
    def __repr__(self):
        return f"Customer C-0{self.id}"



class Rent(db.Model):
    # Rent model representing a dress rental transaction in the database
    id = db.Column(db.Integer, primary_key=True)
    dressId = db.Column(db.Integer, db.ForeignKey('dress.id'))
    clientId = db.Column(db.Integer, db.ForeignKey('customer.id'))
    rentDate = db.Column(db.Date, index=True)
    returnDate = db.Column(db.Date, index=True)
    paymentTotal = db.Column(db.Integer, index=True)
    rentLog = db.Column(db.JSON, nullable=True, default=[])

    dress = db.relationship('Dress', backref='rents')     # One Dress to Many Rents relationship
    customer = db.relationship('Customer', backref='rents')     # One User to Many Rents relationship

    def __init__(self, *args, **kwargs):
        super(Rent, self).__init__(*args, **kwargs)

        if self.dressId:
            self.dress = Dress.query.get(self.dressId)
        if self.clientId:
            self.customer = Customer.query.get(self.clientId)
            
        # Calculate return date based on rentDate value.
        if self.rentDate:
            self.returnDate = self.rentDate + timedelta(days=2)
        # Added Tax.
        tax = self.dress.rentPrice * 0.16
        self.paymentTotal = int(self.dress.rentPrice + tax)

    def is_returned(self):
        # Get the current date and time
        current_datetime = datetime.utcnow()
        # Extract only the date portion from the current date and time
        current_date = current_datetime.date()
        # Check if the current date is greater than or equal to the return date
        return current_date >= self.returnDate
    
    def update_rent_log(self, log):
        existing_rent_log = json.loads(self.rentLog) if self.rentLog else []
        existing_rent_log.append(log)
        self.rentLog = json.dumps(existing_rent_log)
    
    def get_rent_log(self):
        log = []
        if self.rentLog:
            log = json.loads(self.rentLog)
            return log
    
    def __repr__(self):
        return f"Rent R-0{self.id}"
    


class User(UserMixin, db.Model):
    # User model representing a user in the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True)
    email = db.Column(db.String(80), index=True, unique=True)
    name = db.Column(db.String(60), index=True)
    lastName = db.Column(db.String(60), index=True)
    phoneNumber = db.Column(db.Integer, index=True, unique=True)
    password_hash = db.Column(db.String(80))
    joinedAtDate = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    isAdmin = db.Column(db.Boolean, default=False, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        if self.isAdmin:
            return f"ADMIN-0{self.id}"
        else:
            return f"USER-0{self.id}"