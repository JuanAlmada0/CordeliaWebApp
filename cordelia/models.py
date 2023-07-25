from cordelia.db import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
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
    maintenanceStatus = db.Column(db.Boolean, index=True, default=False)
    maintenanceLog = db.Column(db.String, nullable=True, default=None)

    def __init__(self, *args, **kwargs):
        super(Dress, self).__init__(*args, **kwargs)
        self.calculate_rents_for_returns()
    
    def calculate_rents_for_returns(self):
        self.rentsForReturns = self.dressCost // self.rentPrice
    
    def toggle_maintenance_status(self):
        self.maintenanceStatus = not self.maintenanceStatus

    def get_maintenance_log(self):
        maintenance_log = []
        if self.maintenanceLog:
            maintenance_log = json.loads(self.maintenanceLog)
            return maintenance_log
    
    def toggle_rent_status(self):
        self.rentStatus = not self.rentStatus
    
    def increment_times_rented(self):
        self.timesRented += 1
        self.sellable = self.timesRented > self.rentsForReturns

    def decrement_times_rented(self):
        self.timesRented -= 1
        self.sellable = self.timesRented > self.rentsForReturns

    def update_rent_status(self):
        # Query the database to get the latest rent associated with this dress
        associated_rent = Rent.query.filter_by(dressId=self.id).order_by(Rent.rentDate.desc()).first()

        # Check if there is any related rent
        if not associated_rent:
            self.rentStatus = False
        else:
            # Check if the latest rent has been returned
            self.rentStatus = not associated_rent.is_returned()
    
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

    @classmethod
    def update_rent_statuses(cls):
        dresses = cls.query.all()

        for dress in dresses:
            dress.update_rent_status()
            dress.update_times_rented()
            
        logging.debug("update_rent_statuses method executed.")
    
    def __repr__(self):
        return f"ID - D-{self.id}"


class User(UserMixin, db.Model):
    # User model representing a user in the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True, default=None)
    email = db.Column(db.String(80), index=True, unique=True)
    name = db.Column(db.String(60), index=True)
    lastName = db.Column(db.String(60), index=True)
    phoneNumber = db.Column(db.Integer, index=True, unique=True)
    password_hash = db.Column(db.String(80), nullable=True)
    joinedAtDate = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    isAdmin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Will return True if the latest rent has been returned and False if it's still active.
    def check_status(self):
        # Query the database to get the latest rent associated with this user
        associated_rent = Rent.query.filter_by(clientId=self.id).order_by(Rent.rentDate.desc()).first()

        # Check if there is any related rent
        if not associated_rent:
            return False
        else:
            # Check if the latest rent has been returned
            return not associated_rent.is_returned()
    
    def __repr__(self):
        return (f"{self.name} {self.lastName}").title()


class Rent(db.Model):
    # Rent model representing a dress rental transaction in the database
    id = db.Column(db.Integer, primary_key=True)
    dressId = db.Column(db.Integer, db.ForeignKey('dress.id'))
    clientId = db.Column(db.Integer, db.ForeignKey('user.id'))
    rentDate = db.Column(db.Date, index=True)
    returnDate = db.Column(db.Date, index=True)
    paymentTotal = db.Column(db.Integer, index=True)

    dress = db.relationship('Dress', backref='rents')     # One Dress to Many Rents relationship
    user = db.relationship('User', backref='rents')     # One User to Many Rents relationship

    def __init__(self, *args, **kwargs):
        super(Rent, self).__init__(*args, **kwargs)

        if self.dressId:
            self.dress = Dress.query.get(self.dressId)
        if self.clientId:
            self.user = User.query.get(self.clientId)
        # update timesRented and rentStatus value from the related Dress object.
        self.dress.increment_times_rented()
        logging.debug(f"Dress id:{self.dressId} increment_times_rented() method called by created rent id:{self.id}")
        self.dress.toggle_rent_status()
        logging.debug(f"Dress id:{self.dressId} toggle_rent_status() method called by created rent id:{self.id}")
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
        if current_date > self.returnDate:
            return True
        return False

    def __repr__(self):
        return f"ID - R-{self.id}"