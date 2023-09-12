from cordelia.models import Dress, Customer, Rent, Maintenance, maintenance_association
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
        cost = random.randint(rentPrice + 1, rentPrice + 3000)
        marketPrice = random.randint(cost, cost + 3000)
        imageData = None 

        today = datetime.now()
        three_months_ago = today - timedelta(days=3 * 30)
        dateAdded = fake.date_time_between_dates(datetime_start=three_months_ago, datetime_end=today)

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


mexico_area_codes = [
    '55', '81', '33', '664', '662'
]


def generate_unique_phone_number():
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
    three_months_ago = today - timedelta(days=3 * 30)
    dateAdded = fake.date_time_between_dates(datetime_start=three_months_ago, datetime_end=today)

    
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
        dress = Dress.query.filter(
            ~Dress.rents.any(Rent.rentDate >= datetime.now() - timedelta(days=7))
        ).order_by(db.func.random()).first()

        customer = Customer.query.order_by(db.func.random()).first()

        if dress and customer:
            today = datetime.now()
            three_months_ago = today - timedelta(days=3 * 30)

            rent_date = fake.date_time_between_dates(datetime_start=three_months_ago, datetime_end=today)

            payment_method = random.choice(['Credit Card', 'Cash', 'Transfer'])

            new_rent = Rent(
                dressId=dress.id,
                clientId=customer.id,
                rentDate=rent_date,
                paymentMethod=payment_method,
            )

            db.session.add(new_rent)
            db.session.commit()



# def create_weekly_maintenance():
#     # Calculate the maintenance start date (3 months ago from today)
#     today = datetime.utcnow().date()
#     maintenance_start_date = today - timedelta(days=3 * 30)
# 
#     # Iterate through each week in the last 3 months
#     while maintenance_start_date <= today:
#         # Calculate the maintenance date (next Sunday) for the current week
#         days_until_next_sunday = (6 - maintenance_start_date.weekday()) % 7
#         maintenance_date = maintenance_start_date + timedelta(days=days_until_next_sunday)
# 
#         # Get the date range for the past 7 days (last week)
#         last_week_start = maintenance_date - timedelta(days=7)
#         last_week_end = maintenance_date - timedelta(days=1)
# 
#         # Get all returned dresses that were returned in the last 7 days
#         returned_dresses = Dress.query.join(Rent).filter(
#             Rent.returnDate.between(last_week_start, last_week_end)
#         ).all()
# 
#         if returned_dresses:
#             # Randomly select a maintenance type
#             maintenance_type = random.choice(['Cleaning', 'Repair', 'Alteration'])
# 
#             # Generate a random maintenance cost between 50 and 300
#             maintenance_cost = random.randint(80, 300)
# 
#             # Create a Maintenance instance
#             maintenance = Maintenance(
#                 date=maintenance_date,
#                 maintenance_type=maintenance_type,
#                 cost=maintenance_cost
#             )
# 
#             # Link the returned dresses to the maintenance
#             maintenance.dresses.extend(returned_dresses)
# 
#             # Add the maintenance to the database session
#             db.session.add(maintenance)
# 
#             # Move to the next week
#             maintenance_start_date += timedelta(weeks=1)
#     
#     # Commit the changes to the database after creating all maintenance records
#     db.session.commit()



def populate_db():
    with current_app.app_context():
        generate_random_dresses(100)
        generate_random_customers(60)
        generate_sample_rents(80)
        # create_weekly_maintenance()