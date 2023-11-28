from cordelia.models import User, Dress, Customer, Rent, Maintenance
from cordelia.db import db
from datetime import datetime, timedelta
import pytest




@pytest.fixture
def sample_dress():
    dress = Dress(size=4, color='example color', style='example style', brand='example brand', cost=4200, rentPrice=1800)
    return dress


@pytest.fixture
def sample_customer():
    customer = Customer(email='test_customer@example.com', name='test', lastName='customer', phoneNumber=6641234567)
    return customer


def test_create_user(app):
    new_user = User(username='testuser', email='testuser@example.com')
    new_user.set_password('testpassword')

    with app.app_context():
        db.session.add(new_user)
        db.session.commit()

        user = User.query.filter_by(email='testuser@example.com').first()
        assert user is not None
        assert user.email == 'testuser@example.com'
        assert not user.isAdmin
        assert user.check_password('testpassword')


def test_create_dress(app, sample_dress):
    with app.app_context():
        db.session.add(sample_dress)
        db.session.commit()

        dress = Dress.query.filter_by(id=sample_dress.id).first()

        assert dress is not None
        assert dress.rentsForReturns == dress.cost // dress.rentPrice
        assert not dress.maintenanceStatus and not dress.rentStatus


def test_create_customer(app, sample_customer):
    with app.app_context():
        db.session.add(sample_customer)
        db.session.commit()

        customer = Customer.query.filter_by(id=sample_customer.id).first()

        assert customer is not None
        assert customer.dateAdded is not None
        assert not customer.check_status()


def test_create_rent(app, sample_dress, sample_customer):
    with app.app_context():
        db.session.add(sample_dress)
        db.session.add(sample_customer)
        db.session.commit()

        rent_date = datetime.utcnow().date()
        new_rent = Rent(dressId=sample_dress.id, clientId=sample_customer.id, rentDate=rent_date)
        db.session.add(new_rent)
        db.session.commit()

        rent = Rent.query.filter_by(id=new_rent.id).first()

        assert rent is not None
        assert rent.dress == sample_dress
        assert rent.customer == sample_customer
        assert rent.rentDate == rent_date
        assert rent.returnDate == rent_date + timedelta(days=3)
        assert rent.paymentTotal == int(sample_dress.rentPrice + (sample_dress.rentPrice * 0.16))


def test_rent_is_returned(app, sample_dress, sample_customer):
    with app.app_context():
        db.session.add(sample_dress)
        db.session.add(sample_customer)
        db.session.commit()

        rent_date = datetime.utcnow().date() - timedelta(days=5)
        test_rent = Rent(dressId=sample_dress.id, clientId=sample_customer.id, rentDate=rent_date)

        assert test_rent.is_returned()

        rent_date = datetime.utcnow().date()
        test_rent = Rent(dressId=sample_dress.id, clientId=sample_customer.id, rentDate=rent_date)

        assert not test_rent.is_returned()


def test_create_maintenance(app):
    with app.app_context():
        dress1 = Dress(size=4, color='example color 1', style='example style 1', brand='example brand 1', cost=4200, rentPrice=1800)
        dress2 = Dress(size=8, color='example color 2', style='example style 2', brand='example brand 2', cost=4000, rentPrice=1800)
        dress3 = Dress(size=6, color='example color 3', style='example style 3', brand='example brand 3', cost=3800, rentPrice=1700)
        db.session.add(dress1)
        db.session.add(dress2)
        db.session.add(dress3)
        db.session.commit()

        maintenance_date = datetime.utcnow().date()
        maintenance = Maintenance(maintenance_type='Tailor',date=maintenance_date, cost=200)
        db.session.add(maintenance)
        db.session.commit()

        maintenance.dresses.extend([dress1, dress2, dress3])

        maintenance = Maintenance.query.filter_by(id=maintenance.id).first()

        assert maintenance is not None
        assert maintenance.dresses == [dress1, dress2, dress3]
        assert maintenance.dresses[0].size == 4
        assert maintenance.maintenance_type == 'Tailor'


def test_maintenance_is_returned(app):
    with app.app_context():
        dress1 = Dress(size=4, color='example color 1', style='example style 1', brand='example brand 1', cost=4200, rentPrice=1800)
        dress2 = Dress(size=8, color='example color 2', style='example style 2', brand='example brand 2', cost=4000, rentPrice=1800)
        dress3 = Dress(size=6, color='example color 3', style='example style 3', brand='example brand 3', cost=3800, rentPrice=1700)
        db.session.add(dress1)
        db.session.add(dress2)
        db.session.add(dress3)
        db.session.commit()

        maintenance_date = datetime.utcnow().date()
        test_maintenance = Maintenance(maintenance_type='Tailor',date=maintenance_date, cost=200)
        db.session.add(test_maintenance)
        db.session.commit()

        test_maintenance.dresses.extend([dress1, dress2, dress3])

        assert not test_maintenance.is_returned()

        maintenance_date = datetime.utcnow().date() - timedelta(days=5)
        test_maintenance = Maintenance(maintenance_type='Tailor',date=maintenance_date, cost=200)
        db.session.add(test_maintenance)
        db.session.commit()

        test_maintenance.dresses.extend([dress1, dress2, dress3])

        assert test_maintenance.is_returned()