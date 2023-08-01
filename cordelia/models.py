from cordelia.db import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json



class Dress(db.Model):
    # Dress model representing a dress item in the database
    __tablename__ = 'dress'

    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(40), index=True, nullable=False)
    color = db.Column(db.String(40), index=True, nullable=False)
    style = db.Column(db.String(40), index=True, nullable=False)
    brand = db.Column(db.String(40), index=True, nullable=False)
    cost = db.Column(db.Integer, index=True, nullable=False)
    marketPrice = db.Column(db.Integer, index=True, default=None)
    rentPrice = db.Column(db.Integer, index=True, nullable=False)
    rentsForReturns = db.Column(db.Integer, index=True)
    timesRented = db.Column(db.Integer, index=True, default=0)
    sellable = db.Column(db.Boolean, index=True, default=False)
    dateAdded = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    rentStatus = db.Column(db.Boolean, index=True, default=False)
    rentLog = db.Column(db.JSON, default=[])
    maintenanceStatus = db.Column(db.Boolean, index=True, default=False)
    maintenanceLog = db.Column(db.JSON, default=[])
    imageData = db.Column(db.String(255), default=None)

    # Many-to-many relationship with Customer through Rent model
    customers = db.relationship('Customer', secondary='rent', back_populates='dresses', viewonly=True)

    def __init__(self, *args, **kwargs):
        super(Dress, self).__init__(*args, **kwargs)

        self.rentsForReturns = self.cost // self.rentPrice

    def toggle_maintenance_status(self):
        self.maintenanceStatus = not self.maintenanceStatus

    def get_maintenance_log(self):
        log = []
        if self.maintenanceLog:
            # Parse the JSON data stored in 'maintenanceLog' into a Python object
            log = json.loads(self.maintenanceLog)
            # Sort the list of maintenance log dictionaries by the 'date' key in descending order
            log.sort(key=lambda x: x['date'], reverse=True)
            return log
        
    def get_last_maintenance(self):
        if self.maintenanceLog:
            log = json.loads(self.maintenanceLog)
            latest_maintenance_str = max(log, key=lambda x: x['date'])['date']
            # Convert the 'latest_maintenance_str' into a date object
            parsed_date = datetime.strptime(latest_maintenance_str, "%Y-%m-%d").date()
            return parsed_date
    
    def get_rent_log(self):
        log = []
        if self.rentLog:
            log = json.loads(self.rentLog)
            log.sort(key=lambda x: x['date'], reverse=True)
            return log

    def get_last_rent(self):
        if self.rents:
            # Sort the rents by date in descending order to get the latest rent
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            return latest_rent
        else:
            return None
    
    def get_last_customer(self):
        if self.rents:
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            return latest_rent.customer
        else:
            return None

    def check_status(self):
        if self.rents:
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            return not latest_rent.is_returned()
        else:
            return False    

    def update_times_rented(self):
        if self.rents:
            num_of_rents = len(self.rents)
            # Update the timesRented and sellable attributes
            self.timesRented = num_of_rents
            self.sellable = num_of_rents > self.rentsForReturns
        else:
            self.timesRented = 0
            self.sellable = self.timesRented > self.rentsForReturns

    def update_rent_status(self):
        if self.rents:
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            # Check if the latest rent has been returned
            self.rentStatus = not latest_rent.is_returned()
        else:
            self.rentStatus = False
    
    def update_rent_log(self):
        rent_log = []
        for rent in self.rents:
            if rent.customer:
                customer_info = {
                    "id": f"D-{rent.customer.id:02}",
                    "last_name": rent.customer.lastName,
                    "name": rent.customer.name
                }
                rent_log_entry = {
                    "date": rent.rentDate.strftime('%Y-%m-%d'),
                    "id": f"R-{rent.id:02}",
                    "customer_info": customer_info
                }
                rent_log.append(rent_log_entry)

        self.rentLog = json.dumps(rent_log)

    @classmethod
    def update_rent_statuses(cls):
        dresses = cls.query.all()

        for dress in dresses:
            dress.update_rent_status()
            dress.update_times_rented()
            dress.update_rent_log()      
    
    def __repr__(self):
        return f"Dress D-{self.id:02}"
    

class Customer(db.Model):
    # User model representing a user in the database
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), index=True, unique=True)
    name = db.Column(db.String(40), index=True, nullable=False)
    lastName = db.Column(db.String(40), index=True, nullable=False)
    phoneNumber = db.Column(db.Integer, index=True, unique=True)
    dateAdded = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    rentLog = db.Column(db.JSON, nullable=True, default=[])

    # Many-to-many relationship with Dress through Rent model
    dresses = db.relationship('Dress', secondary='rent', back_populates='customers', viewonly=True)
    
    def check_status(self):
        if self.rents:
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            return not latest_rent.is_returned()
        else:
            return False
        
    def get_last_rent(self):
        if self.rents:
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            return latest_rent.rentDate 
        else:
            return None
    
    def update_rent_log(self):
        rent_log = []
        for rent in self.rents:
            if rent.dress:
                dress_info = {
                    "id": f"D-{rent.dress.id:02}",
                    "brand": rent.dress.brand,
                    "style": rent.dress.style,
                    "size": rent.dress.size
                }
                rent_log_entry = {
                    "date": rent.rentDate.strftime('%Y-%m-%d'),
                    "id": f"R-{rent.id:02}",
                    "total": f"Total: ${rent.paymentTotal}",
                    "dress_info": dress_info
                }
                rent_log.append(rent_log_entry)

        self.rentLog = json.dumps(rent_log)
    
    def get_rent_log(self):
        log = []
        if self.rentLog:
            log = json.loads(self.rentLog)
            log.sort(key=lambda x: x['date'], reverse=True)
            return log
        
    @classmethod
    def update_rent_logs(cls):
        customers = cls.query.all()

        for customer in customers:
            customer.update_rent_log()

    def __repr__(self):
        return f"Customer C-{self.id:02}"


class Rent(db.Model):
    # Rent model representing a dress rental transaction in the database
    __tablename__ = 'rent'

    id = db.Column(db.Integer, primary_key=True)
    dressId = db.Column(db.Integer, db.ForeignKey('dress.id'))
    clientId = db.Column(db.Integer, db.ForeignKey('customer.id'))
    rentDate = db.Column(db.Date, index=True, nullable=False)
    returnDate = db.Column(db.Date, index=True)
    paymentTotal = db.Column(db.Integer, index=True)
    rentLog = db.Column(db.JSON, default=[])

    # Many Dress to Many Customer relationship associated through dressId and clientId.

    dress = db.relationship('Dress', backref='rents')     # One Dress to Many Rents relationship for Dress
    customer = db.relationship('Customer', backref='rents')     # One User to Many Rents relationship for Customer

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
        current_datetime = datetime.utcnow()
        # Extract only the date portion from the current date and time
        current_date = current_datetime.date()
        # Return True if current date is greater than or equal to the return date
        return current_date > self.returnDate
    
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
        return f"Rent R-{self.id:02}"
    

class User(UserMixin, db.Model):
    # User model representing a user in the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), index=True, unique=True)
    email = db.Column(db.String(80), index=True, unique=True)
    name = db.Column(db.String(40), index=True)
    lastName = db.Column(db.String(40), index=True)
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
            return f"ADMIN-{self.id:02}"
        else:
            return f"USER-{self.id:02}"