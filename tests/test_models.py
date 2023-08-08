from cordelia.models import User, Dress, Customer, Rent
from cordelia.db import db
from datetime import datetime, timedelta



def test_create_user(app):
    new_user = User(username='testuser', email='testuser@example.com', isAdmin=True)
    new_user.set_password('testpassword')

    with app.app_context():
        db.session.add(new_user)
        db.session.commit()

        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'testuser@example.com'
        assert user.isAdmin
        assert user.check_password('testpassword')



def test_create_dress(app):
    new_dress = Dress(size=4, color='example color', style='example style', brand='example brand', cost=4200, rentPrice=1800)
    
    with app.app_context():
        db.session.add(new_dress)
        db.session.commit()

        dress = Dress.query.filter_by(id=new_dress.id).first()

        assert dress is not None
        assert dress.rentsForReturns == dress.cost // dress.rentPrice
        assert not dress.maintenanceStatus and not dress.rentStatus



def test_create_customer(app):
    new_customer = Customer(email='test_customer@example.com', name='test', lastName='customer', phoneNumber=6641234567)

    with app.app_context():
        db.session.add(new_customer)
        db.session.commit()

        customer = Customer.query.filter_by(id=new_customer.id).first()

        assert customer is not None
        assert customer.dateAdded is not None
        assert not customer.check_status()



def test_create_rent(app):
    with app.app_context():
        dress = Dress(size=4, color='example color', style='example style', brand='example brand', cost=4200, rentPrice=1800)
        customer = Customer(name='Test',lastName='Customer', email='test@example.com')
        db.session.add(dress)
        db.session.add(customer)
        db.session.commit()

        rent_date = datetime.utcnow().date()
        new_rent = Rent(dressId=dress.id, clientId=customer.id, rentDate=rent_date)
        db.session.add(new_rent)
        db.session.commit()

        rent = Rent.query.filter_by(id=new_rent.id).first()

        assert rent is not None
        assert rent.dress == dress
        assert rent.customer == customer
        assert rent.rentDate == rent_date
        assert rent.returnDate == rent_date + timedelta(days=3)
        assert rent.paymentTotal == int(dress.rentPrice + (dress.rentPrice * 0.16))



def test_rent_is_returned(app):
    with app.app_context():
        dress = Dress(size=4, color='example color', style='example style', brand='example brand', cost=4200, rentPrice=1800)
        customer = Customer(name='Test', lastName='Customer', email='test@example.com')
        db.session.add(dress)
        db.session.add(customer)
        db.session.commit()

        # Test rent with a return date in the past (already returned)
        rent_date = datetime.utcnow().date() - timedelta(days=5)  # Rent date 5 days ago
        test_rent = Rent(dressId=dress.id, clientId=customer.id, rentDate=rent_date)

        # Should return True since the return date is in the past
        assert test_rent.is_returned()

        # Test rent with a return date in the future (not yet returned)
        rent_date = datetime.utcnow().date()  # Rent date today
        test_rent = Rent(dressId=dress.id, clientId=customer.id, rentDate=rent_date)

        # Should return False since the return date is in the future
        assert not test_rent.is_returned()