from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField, IntegerField, 
    SelectField, DateField, HiddenField
    )
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional
from wtforms.validators import ValidationError
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
import json
from cordelia.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
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
    submit = SubmitField('Login')


class SearchForm(FlaskForm):
    category = SelectField('Category', choices=[], default='Select', validators=[DataRequired()])
    search = StringField('Search')
    submit = SubmitField('Filter')
    
    def __init__(self, model_columns, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.category.choices = [('Select', 'Select')] + [(column, column) for column in model_columns]


class UserRentForm(FlaskForm):
    rentDate = DateField('Rent Date', validators=[DataRequired()])
    submit = SubmitField('Check Out')


class MaintenanceForm(FlaskForm):
    dress_id = HiddenField('Dress ID', validators=[DataRequired()])
    maintenanceDate = DateField('Maintenance Date', validators=[DataRequired()])
    maintenanceType = StringField('Maintenance Type', validators=[DataRequired()])
    maintenanceCost = IntegerField('Cost', validators=[NumberRange(min=0)])
    submit = SubmitField('Maintenance')

class DeleteForm(FlaskForm):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Delete')


class DressForm(FlaskForm):
    brand = StringField('Brand', validators=[DataRequired()])
    size = StringField('Size', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    style = StringField('Style', validators=[DataRequired()])
    dressCost = IntegerField('Dress Cost', validators=[DataRequired()])
    marketPrice = IntegerField('Market Price', validators=[Optional()])
    rentPrice = IntegerField('Rent Price', validators=[DataRequired()])
    submit = SubmitField('Submit')


class RentForm(FlaskForm):
    userId = IntegerField('User Id', validators=[DataRequired()])
    dressId = IntegerField('Dress Id', validators=[DataRequired()])
    rentDate = DateField('Rent Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UserForm(FlaskForm):
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

            # Store the parsed phone number in the form field
            field.data = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

        except NumberParseException:
            raise ValidationError('Invalid phone number')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already exists.')

    def validate_phoneNumber_duplicate(self, field):
        if User.query.filter_by(phoneNumber=field.data).first():
            raise ValidationError('Phone number already exists.')