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
    dressDescription = db.Column(db.String(30), index=True, nullable=False)
    brand = db.Column(db.String(20), index=True, nullable=False)
    dressCost = db.Column(db.Integer, index=True, nullable=False)
    marketPrice = db.Column(db.Integer, nullable=False)
    rentPrice = db.Column(db.Integer, index=True, nullable=False)
    rentsToReturnInvestment = db.Column(db.Integer)
    timesRented = db.Column(db.Integer, default=0)
    sellable = db.Column(db.Boolean, default=False)
    rentStatus = db.Column(db.Boolean, default=False)

    def __init__(self, *args, **kwargs):
        super(Dress, self).__init__(*args, **kwargs)
        self.calculate_rents_to_return_investment()

    def __repr__(self):
        return f"Dress ID: {self.id}, Brand: {self.brand}"
    
    def calculate_rents_to_return_investment(self):
        self.rentsToReturnInvestment = self.dressCost // self.rentPrice

    def increment_times_rented(self):
        # Method to increment the timesRented value and update sellable flag
        try:
            if self.timesRented is not None:
                self.timesRented += 1
                self.sellable = self.timesRented > self.rentsToReturnInvestment
            else:
                self.timesRented = 1
                self.sellable = False
        except Exception as e:
            print("Error in increment_times_rented: ", e)

    def update_rent_status(self):
        try:
            self.rentStatus = True
        except Exception as e:
            print("Error in update_rent_status: ", e)


class User(UserMixin, db.Model):
    # User model representing a user in the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True)
    email = db.Column(db.String(80), index=True, unique=True)
    name = db.Column(db.String(60), index=True)
    lastName = db.Column(db.String(60), index=True)
    phoneNumber = db.Column(db.Integer, unique=True)
    password_hash = db.Column(db.String(80))
    joinedAtDate = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    isAdmin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<{self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Rent(db.Model):
    # Rent model representing a dress rental transaction in the database
    id = db.Column(db.Integer, primary_key=True)
    dressId = db.Column(db.Integer, db.ForeignKey('dress.id'))
    clientId = db.Column(db.Integer, db.ForeignKey('user.id'))
    rentDate = db.Column(db.Date, index=True)
    returnDate = db.Column(db.Date, index=True)
    paymentTotal = db.Column(db.Integer, nullable=True)

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
        # Update rentStatus from Dress Instance.
        self.dress.update_rent_status()
        # Calculate return date based on rentDate value.
        if self.rentDate:
            self.returnDate = self.rentDate + timedelta(days=5)
        # Added Tax.
        tax = self.dress.rentPrice * 0.16
        self.paymentTotal = int(self.dress.rentPrice + tax)

    def __repr__(self):
        return f"<Rent id={self.id}, dressId-{self.dressId}, clientId={self.clientId}>"