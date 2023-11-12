from cordelia.db import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin



class Dress(db.Model):
    # Dress model representing a dress item in the database
    __tablename__ = 'dress'

    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.Integer, index=True, nullable=False)
    color = db.Column(db.String(15), index=True, nullable=False)
    style = db.Column(db.String(15), index=True, nullable=False)
    brand = db.Column(db.String(20), index=True, nullable=False)
    cost = db.Column(db.Integer, index=True, nullable=False)
    marketPrice = db.Column(db.Integer, index=True, default=None)
    rentPrice = db.Column(db.Integer, index=True, nullable=False)
    rentsForReturns = db.Column(db.Integer, index=True)
    sellable = db.Column(db.Boolean, index=True, default=False)
    dateAdded = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    timesRented = db.Column(db.Integer, index=True, default=0)
    rentStatus = db.Column(db.Boolean, index=True, default=False)
    maintenanceStatus = db.Column(db.Boolean, index=True, default=False)
    imageData = db.Column(db.String(255), default=None)
    sold = db.Column(db.Boolean, index=True, default=False)

    customers = db.relationship('Customer', secondary='rent', back_populates='dresses', viewonly=True) # Many-to-many relationship with Customer through Rent model
    sale = db.relationship('DressSale', back_populates='dress')

    def __init__(self, *args, **kwargs):
        super(Dress, self).__init__(*args, **kwargs)

        self.rentsForReturns = self.cost // self.rentPrice
        
    def get_last_maintenance(self):
        if self.maintenances:
            sorted_maintenances = sorted(self.maintenances, key=lambda maintenance: maintenance.date, reverse=True)

            latest_maintenance = sorted_maintenances[0]

            return latest_maintenance
        else:
            return None
    
    def update_maintenance_status(self):
        if self.rents:
            sorted_maintenances = sorted(self.maintenances, key=lambda maintenance: maintenance.date, reverse=True)
            latest_maintenance = sorted_maintenances[0]

            # Check if the latest rent has been returned
            self.maintenanceStatus = not latest_maintenance.is_returned()
        else:
            self.maintenanceStatus = False
    
    def check_maintenance_status(self):
        if self.maintenances:
            sorted_maintenances = sorted(self.maintenances, key=lambda maintenance: maintenance.date, reverse=True)
            latest_maintenance = sorted_maintenances[0]

            return not latest_maintenance.is_returned()
        else:
            return False

    def get_last_rent(self):
        if self.rents:
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
        
    def update_rent_status(self):
        if self.rents:
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            self.rentStatus = not latest_rent.is_returned()
        else:
            self.rentStatus = False

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

    @classmethod
    def update_statuses(cls):
        dresses = cls.query.all()

        for dress in dresses:
            if dress.rents:
                dress.update_times_rented()
                dress.update_rent_status()
            if dress.maintenances:
                dress.update_maintenance_status()
    
    def __repr__(self):
        return f"D-{self.id:02}"



# Association table for the many-to-many relationship between Dress and Maintenance
maintenance_association = db.Table('maintenance_association',
    db.Column('maintenance_id', db.Integer, db.ForeignKey('maintenance.id'), primary_key=True),
    db.Column('dress_id', db.Integer, db.ForeignKey('dress.id'), primary_key=True)
)



class Maintenance(db.Model):
    # Maintenance model representing maintenances for dresses in the database
    __tablename__ = 'maintenance'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, index=True, nullable=False)
    returnDate = db.Column(db.Date, index=True)
    maintenance_type = db.Column(db.String(20), index=True, nullable=False)
    cost = db.Column(db.Integer(), index=True, nullable=False)
    
    dresses = db.relationship('Dress', secondary=maintenance_association, backref='maintenances') # Many Dresses to One Maintenace relationship

    def __init__(self, *args, **kwargs):
        super(Maintenance, self).__init__(*args, **kwargs)

        if self.date:
            self.returnDate = self.date + timedelta(days=2)
    
    def is_returned(self):
        current_datetime = datetime.utcnow()
        current_date = current_datetime.date()

        return current_date > self.returnDate if self.returnDate else False

    def __repr__(self):
        return f"M-{self.id:02}"



class Customer(db.Model):
    # Customer model representing a customer in the database
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40), index=True, unique=True)
    name = db.Column(db.String(30), index=True, nullable=False)
    lastName = db.Column(db.String(30), index=True, nullable=False)
    phoneNumber = db.Column(db.Integer, index=True, unique=True)
    dateAdded = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

    dresses = db.relationship('Dress', secondary='rent', back_populates='customers', viewonly=True) # Many-to-many relationship with Dress through Rent model
    sales = db.relationship('DressSale', back_populates='customer')

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
    
    def get_last_dress(self):
        if self.rents:
            sorted_rents = sorted(self.rents, key=lambda rent: rent.rentDate, reverse=True)
            latest_rent = sorted_rents[0]

            return latest_rent.dress
        else:
            return None

    def __repr__(self):
        return f"C-{self.id:02}"



class Rent(db.Model):
    # Rent model representing a dress rental transaction in the database
    __tablename__ = 'rent'

    id = db.Column(db.Integer, primary_key=True)
    dressId = db.Column(db.Integer, db.ForeignKey('dress.id'))
    clientId = db.Column(db.Integer, db.ForeignKey('customer.id'))
    rentDate = db.Column(db.Date, index=True, nullable=False)
    returnDate = db.Column(db.Date, index=True)
    paymentMethod = db.Column(db.String(20), index=True, nullable=False)
    paymentTotal = db.Column(db.Integer, index=True)

    # Many Dress to Many Customer relationship associated through dressId and clientId.

    dress = db.relationship('Dress', backref='rents')     # One Dress to Many Rents relationship for Dress
    customer = db.relationship('Customer', backref='rents')     # One User to Many Rents relationship for Customer

    def __init__(self, *args, **kwargs):
        super(Rent, self).__init__(*args, **kwargs)

        if self.dressId:
            self.dress = Dress.query.filter_by(id=self.dressId).first()
             
        if self.clientId:
            self.customer = Customer.query.filter_by(id=self.clientId).first()
            
        if not self.returnDate:
            self.returnDate = self.rentDate + timedelta(days=3)

        # Added Tax.
        if self.dress:
            tax = self.dress.rentPrice * 0.16
            self.paymentTotal = int(self.dress.rentPrice + tax)

    def is_returned(self):
        current_datetime = datetime.utcnow()
        current_date = current_datetime.date()

        return current_date > self.returnDate if self.returnDate else False
    
    def __repr__(self):
        return f"R-{self.id:02}"
    


class DressSale(db.Model):
    # Sale model representing Dress sales.
    __tablename__ = 'dress_sale'
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, index=True, nullable=False)
    sale_price = db.Column(db.Integer, index=True, nullable=False)

    # Relationships
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer', back_populates='sales')

    dress_id = db.Column(db.Integer, db.ForeignKey('dress.id'), nullable=False)
    dress = db.relationship('Dress', back_populates='sale')

    def __repr__(self):
        return f"DressSale-{self.id:02}"



class User(UserMixin, db.Model):
    # User model representing a user in the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), index=True, unique=True)
    email = db.Column(db.String(60), index=True, unique=True)
    name = db.Column(db.String(30), index=True)
    lastName = db.Column(db.String(30), index=True)
    phoneNumber = db.Column(db.Integer, index=True, unique=True)
    password_hash = db.Column(db.String(128))
    joinedAtDate = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    isAdmin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        if self.isAdmin:
            return f"ADMIN-{self.id:02}"
        else:
            return f"USER-{self.id:02}"