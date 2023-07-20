from cordelia.db import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin



class Dress(db.Model):
    # Dress model representing a dress item in the database
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(20), index=True, nullable=False)
    color = db.Column(db.String(20), index=True, nullable=False)
    style = db.Column(db.String(20), index=True, nullable=False)
    brand = db.Column(db.String(20), index=True, nullable=False)
    dressCost = db.Column(db.Integer, index=True, nullable=False)
    marketPrice = db.Column(db.Integer, index=True, nullable=True)
    rentPrice = db.Column(db.Integer, index=True, nullable=False)
    rentsToReturnInvestment = db.Column(db.Integer, index=True)
    timesRented = db.Column(db.Integer, index=True, default=0)
    sellable = db.Column(db.Boolean, index=True, default=False)
    rentStatus = db.Column(db.Boolean, index=True, default=False)

    def __init__(self, *args, **kwargs):
        super(Dress, self).__init__(*args, **kwargs)
        self.calculate_rents_to_return_investment()
    
    def calculate_rents_to_return_investment(self):
        self.rentsToReturnInvestment = self.dressCost // self.rentPrice
     # Methods to modify the timesRented value and update sellable flag
    def increment_times_rented(self):
        if self.timesRented is not None:
            self.timesRented += 1
            self.sellable = self.timesRented > self.rentsToReturnInvestment
        else:
            self.timesRented = 1
            self.sellable = False

    def decrement_times_rented(self):
        self.timesRented -= 1
        self.sellable = self.timesRented > self.rentsToReturnInvestment

    def update_times_rented(self):
        associatedRents = Rent.query.filter_by(dressId=self.id).all()
        numOfRents = 0
        if associatedRents:
            for rent in associatedRents:
                numOfRents += 1
            self.timesRented = numOfRents
            self.sellable = self.timesRented > self.rentsToReturnInvestment
        else:
            self.timesRented = 0
            self.sellable = self.timesRented > self.rentsToReturnInvestment

    def update_rent_status(self):
        # Query the database to get the latest rent associated with this dress
        associated_rent = Rent.query.filter_by(dressId=self.id).order_by(Rent.rentDate.desc()).first()

        # Check if there is any related rent
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
    
    def __repr__(self):
        return f"Dress Id - {self.id}"


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
    isAdmin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def check_status(self):
        # Query the database to get the latest rent associated with this user
        associated_rent = Rent.query.filter_by(dressId=self.id).order_by(Rent.rentDate.desc()).first()

        # Check if there is any related rent
        if not associated_rent:
            return False
        else:
            # Check if the latest rent has been returned
            return not associated_rent.is_returned()
    
    def __repr__(self):
        return f"{self.username}"


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
        # Increment timesRented value from the Dress instance.
        self.dress.increment_times_rented()
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
        return f"Rent Id - {self.id}"