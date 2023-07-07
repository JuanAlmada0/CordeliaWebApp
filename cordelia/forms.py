from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.validators import ValidationError
import phonenumbers



class UserRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
    name = StringField('First name', validators=[DataRequired()])
    lastName = StringField('Last name', validators=[DataRequired()])
    phoneNumber = StringField('Phone Number')
    submit = SubmitField('Register')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def validate_phone_number(self, field):
        phone_number = field.data
        try:
            input_number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(input_number):
                raise ValidationError('Invalid phone number')
    
            field.data = phone_number  # Set the validated phone number back to the field
    
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError('Invalid phone number')
