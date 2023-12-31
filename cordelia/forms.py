from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField, IntegerField, 
    SelectField, DateField, HiddenField, FileField, FieldList, FormField
    )
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from flask_wtf.file import FileAllowed
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from cordelia.models import User, Customer, Dress


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
    name = StringField('First name', validators=[DataRequired()])
    lastName = StringField('Last name', validators=[DataRequired()])
    phoneNumber = StringField('Phone Number', validators=[DataRequired()])
    next = HiddenField()
    submit = SubmitField('Register')

    def validate_phoneNumber(self, field):
        phone_number = field.data
        try:
            parsed_number = phonenumbers.parse(phone_number, "MX")
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError('Invalid phone number')

            # Store the parsed phone number in the form field
            field.data = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

        except NumberParseException:
            raise ValidationError('Invalid phone number')
    # Check if the username, email or phone already exists in the database    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already exists.')

    def validate_phoneNumber_duplicate(self, field):
        if User.query.filter_by(phoneNumber=field.data).first():
            raise ValidationError('Phone number already exists.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    next = HiddenField() 
    submit = SubmitField('Login')


class SearchForm(FlaskForm):
    category = SelectField('Category', choices=[], default=('Select','Select'), validators=[DataRequired()])
    search = StringField('Search')
    submit = SubmitField('Filter')
    
    def __init__(self, model_columns, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.category.choices = [('Select', 'Select')] + [(column, column) for column in model_columns]


class DressIdForm(FlaskForm):
    dress_id = IntegerField('Dress ID', validators=[Optional()])


class MaintenanceForm(FlaskForm):
    dress_ids = FieldList(FormField(DressIdForm), min_entries=1)
    maintenanceDate = DateField('Date')
    maintenanceType = SelectField('Type', choices=[('None', None), ('Cleaning', 'Cleaning'), ('Repair', 'Repair'), ('Alteration', 'Alteration')])
    maintenanceCost = IntegerField('Cost')
    submit = SubmitField('Submit')


class SaleForm(FlaskForm):
    sale_date = DateField('Sale Date')
    sale_price = IntegerField('Sale Price')
    dress_id = SelectField('Dress', coerce=int)
    customer_id = SelectField('Customer', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)

        # Populate dress choices
        self.dress_id.choices = [(dress.id, f'D-{dress.id:02}') for dress in Dress.query.all()]

        # Populate customer choices
        self.customer_id.choices = [(customer.id, f'C-{customer.id:02}') for customer in Customer.query.all()]


class DeleteForm(FlaskForm):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Delete')


class DressForm(FlaskForm):
    brand = StringField('Brand', validators=[DataRequired()])
    size = IntegerField('Size', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    style = StringField('Style', validators=[DataRequired()])
    cost = IntegerField('Dress Cost', validators=[DataRequired()])
    marketPrice = IntegerField('Market Price', validators=[Optional()])
    rentPrice = IntegerField('Rent Price', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'])])
    submit = SubmitField('Submit')


class CustomerForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('First name', validators=[DataRequired()])
    lastName = StringField('Last name', validators=[DataRequired()])
    phoneNumber = StringField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_phoneNumber(self, field):
        phone_number = field.data
        try:
            parsed_number = phonenumbers.parse(phone_number, "MX")
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError('Invalid phone number')

            field.data = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

        except NumberParseException:
            raise ValidationError('Invalid phone number')

    def validate_email(self, field):
        if Customer.query.filter_by(email=field.data).first():
            raise ValidationError('Email already exists.')

    def validate_phoneNumber_duplicate(self, field):
        if Customer.query.filter_by(phoneNumber=field.data).first():
            raise ValidationError('Phone number already exists.')
        

class RentForm(FlaskForm):
    customerId = IntegerField('Customer Id', validators=[DataRequired()])
    dressId = IntegerField('Dress Id', validators=[DataRequired()])
    rentDate = DateField('Rent Date', validators=[DataRequired()])
    paymentMethod = SelectField('Payment Method', choices=[('Transfer', 'Transfer'), ('Cash', 'Cash'), ('Credit Card', 'Credit Card')])
    submit = SubmitField('Submit')


class UserRentForm(FlaskForm):
    rentDate = DateField('Rent Date', validators=[DataRequired()])
    submit = SubmitField('Check Out')