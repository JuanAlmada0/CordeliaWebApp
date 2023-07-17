from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.validators import ValidationError
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from cordelia.models import User, Dress



class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
    name = StringField('First name', validators=[DataRequired()])
    lastName = StringField('Last name', validators=[DataRequired()])
    phoneNumber = StringField('Phone Number')
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


class InventoryForm(FlaskForm):
    brand = StringField('Brand', validators=[DataRequired()])
    size = StringField('Size', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    style = StringField('Style', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    dressCost = IntegerField('Dress Cost', validators=[DataRequired()])
    marketPrice = IntegerField('Market Price', validators=[DataRequired()])
    rentPrice = IntegerField('Rent Price', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    category = SelectField('Category', choices=[], default='Select Category', validators=[DataRequired()])
    search = StringField('Search')
    submit = SubmitField('Filter')
    
    def __init__(self, model_columns, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.category.choices = [('Select Category', 'Select Category')] + [(column, column) for column in model_columns]


class RentForm(FlaskForm):
    rentDate = DateField('Rent Date')
    submit = SubmitField('Check Out')