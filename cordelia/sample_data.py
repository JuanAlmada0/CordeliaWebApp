from cordelia.models import Dress, Customer, Rent, Maintenance
from cordelia.db import db
from faker import Faker
import random
from flask import current_app
from datetime import datetime, timedelta
from sqlalchemy.orm.exc import NoResultFound


fake = Faker()


def generate_random_dresses(num_dresses):
    for _ in range(num_dresses):
        size = random.randint(2, 12)
        color = fake.color_name()
        style = random.choice([
                        "A-Line", "Sheath", "Shift", "Wrap", "Maxi", "Midi", "Mini", "Bodycon", "Fit and Flare",
                        "Empire Waist", "Mermaid", "Ball Gown", "Tunic", "Off-the-Shoulder", "Halter",
                        "Peplum", "Pencil", "High-Low", "Tea Length", "Sweater Dress"
                    ])
        brand = random.choice([
                    "Chanel", "Gucci", "Louis Vuitton", "Prada", "Dior", "Versace", "Fendi", "Burberry", "Givenchy",
                    "Valentino", "Balenciaga", "Hermès", "Alexander McQueen", "Celine", "Stella McCartney",
                    "H&M", "Zara", "Forever 21", "Urban Outfitters", "Topshop", "Mango", "Charlotte Russe",
                    "Express", "Lululemon Athletica"
                    ])
        rentPrice = random.choice(range(1300, 2001, 100))
        cost = random.randint(rentPrice + 100, rentPrice + 2100)
        marketPrice = random.randint(cost, cost + 2000)
        imageData = None 

        today = datetime.now()
        fourMonthsAgo = today - timedelta(days=6 * 30)
        dateAdded = fake.date_time_between_dates(datetime_start=fourMonthsAgo, datetime_end=today)

        try:
            # Check if a dress with the same attributes exists
            existing_dress = Dress.query.filter_by(
                size=size,
                color=color,
                style=style,
                brand=brand
            ).one()
        except NoResultFound:
            # If no matching dress found, create and add a new dress
            dress = Dress(
                size=size,
                color=color,
                style=style,
                brand=brand,
                cost=cost,
                marketPrice=marketPrice,
                rentPrice=rentPrice,
                dateAdded=dateAdded,
                imageData=imageData
            )
            
            db.session.add(dress)
    
    db.session.commit()


def generate_unique_email():
    while True:
        email = fake.email()
        existing_customer = Customer.query.filter_by(email=email).first()
        if not existing_customer:
            return email



def generate_unique_phone_number():
    mexico_area_codes = [
    '55', '81', '33', '664', '662'
    ]
    while True:
        area_code = random.choice(mexico_area_codes)
        local_number = fake.random_int(min=1000000, max=9999999)
        phone_number = f'{area_code}{local_number}'
        existing_customer = Customer.query.filter_by(phoneNumber=phone_number).first()
        if not existing_customer:
            return phone_number


def generate_random_customer():
    email = generate_unique_email()
    name = fake.first_name()
    last_name = fake.last_name()
    phone_number = generate_unique_phone_number()

    today = datetime.now()
    fourMonthsAgo = today - timedelta(days=6 * 30)
    dateAdded = fake.date_time_between_dates(datetime_start=fourMonthsAgo, datetime_end=today)
    

    customer = Customer(
        email=email,
        name=name,
        lastName=last_name,
        phoneNumber=phone_number,
        dateAdded=dateAdded
    )
    
    return customer



def generate_random_customers(num_customers):
    for _ in range(num_customers):
        customer = generate_random_customer()
        db.session.add(customer)
    
    db.session.commit()



def generate_sample_rents(num_rents):
    for _ in range(num_rents):
        dress = random.choice(Dress.query.all())
        customer = Customer.query.order_by(db.func.random()).first()

        if dress and customer:
            today = datetime.now()
            four_months_ago = today - timedelta(days=6 * 30)

            rent_date = fake.date_time_between_dates(datetime_start=four_months_ago, datetime_end=today)

            payment_method = random.choice(['Credit Card', 'Cash', 'Transfer'])

            new_rent = Rent(
                dressId=dress.id,
                clientId=customer.id,
                rentDate=rent_date,
                paymentMethod=payment_method,
            )

            db.session.add(new_rent)
            db.session.commit()



def create_weekly_maintenance():
    today = datetime.utcnow().date()
    firstDayOfTheWeek = datetime.utcnow().date() - timedelta(days = 6 * 30)
    lastDayOfTheWeek = firstDayOfTheWeek + timedelta(days=7)
    while lastDayOfTheWeek < today :
        # Get all returned dresses that were returned in the 7 days between first and last day
        returned_dresses = Dress.query.join(Rent).filter(
            Rent.returnDate.between(firstDayOfTheWeek, lastDayOfTheWeek)
        ).all()
        for dress in returned_dresses:
            if len(dress.maintenances) == len(dress.rents):
                returned_dresses.remove(dress)

        if returned_dresses:
            maintenance_type = random.choice(['Cleaning', 'Repair', 'Alteration'])
            maintenance_cost = 80 * len(returned_dresses)

            maintenance = Maintenance(
                date = lastDayOfTheWeek,
                maintenance_type = maintenance_type,
                cost = maintenance_cost
            )
            # Link the returned dresses to the maintenance object
            maintenance.dresses.extend(returned_dresses)

            db.session.add(maintenance)
            db.session.commit()

        lastDayOfTheWeek += timedelta(weeks=1)
        firstDayOfTheWeek += timedelta(weeks=1)
    


def populate_db():
    with current_app.app_context():
        generate_random_dresses(70)
        generate_random_customers(80)
        generate_sample_rents(125)
        create_weekly_maintenance()