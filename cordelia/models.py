from .db import db
from datetime import datetime



class Dress(db.Model):
    # Dress model representing a dress item in the database
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(20), index=True, nullable=False)
    color = db.Column(db.String(20), index=True, nullable=False)
    style = db.Column(db.String(20), index=True, nullable=False)
    dressDescription = db.Column(db.String(30), index=True, nullable=False)
    brand = db.Column(db.String(20), index=True, nullable=False)
    boughtPrice = db.Column(db.Integer, index=True, nullable=False)
    marketPrice = db.Column(db.Integer, nullable=False)
    rentPrice = db.Column(db.Integer, index=True, nullable=False)
    rentsToReturnInvest = db.Column(db.Integer, nullable=False)
    timesRented = db.Column(db.Integer, default=0)
    sellable = db.Column(db.Boolean, default=False)

    def increment_times_rented(self):
        # Method to increment the timesRented value and update sellable flag
        if self.timesRented is not None:
            self.timesRented += 1
            self.sellable = self.timesRented > self.rentsToReturnInvestment
        else:
            self.timesRented = 1
            self.sellable = False



class User (db.Model):
    # User model representing a user in the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True)
    email = db.Column(db.String(80), index=True, unique=True)
    name = db.Column(db.String(60), index=True)
    lastName = db.Column(db.String(60), index=True)
    phoneNumber = db.Column(db.Integer, unique=True)
    password_hash = db.Column(db.String(80))
    joinedAtDate = db.Column(db.DateTime(), index=True, default=datetime.utcnow)



class Rent(db.Model):
    # Rent model representing a dress rental transaction in the database
    id = db.Column(db.Integer, primary_key=True)
    dressId = db.Column(db.Integer, db.ForeignKey('dress.id'))
    clientId = db.Column(db.Integer, db.ForeignKey('user.id'))
    price = db.Column(db.Integer, index=True, nullable=False)
    rentDate = db.Column(db.Date, index=True, nullable=False)
    returnDate = db.Column(db.Date, index=True, nullable=True, default=None)
    paymentDate = db.Column(db.String(20), index=True, nullable=True)
    paymentTotal = db.Column(db.Integer, nullable=True)

    dress = db.relationship('Dress', backref='rents')     # One Dress to Many Rents relationship
    user = db.relationship('User', backref='rents')     # One User to Many Rents relationship

    def __init__(self, *args, **kwargs):
        super(Rent, self).__init__(*args, **kwargs)
        # Increment timesRented value from the Dress instance.
        self.dress.increment_times_rented()
        # Added Tax.
        dress = self.dress
        tax = dress.rentPrice * 0.16
        self.paymentTotal = int(dress.rentPrice + tax)