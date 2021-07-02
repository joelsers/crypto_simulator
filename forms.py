from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from wtforms.fields.html5 import DecimalRangeField


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired(), Length(min=6)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    USDT = FloatField('USDT to start with. You cannot update this later.' , validators = [DataRequired("How much USD do you want to start with? This must be a number between 10 and 1,000,000"), NumberRange(min =10, max = 1000000)])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class BuyForm(FlaskForm):
    amount = DecimalRangeField('Amount to buy', validators = [DataRequired()])

class SellForm(FlaskForm):
    amount = DecimalRangeField('Amount to sell', validators = [DataRequired()])
    