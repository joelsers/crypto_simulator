from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Email, Length



class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired(), Length(min=6)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    USDT = FloatField('USDT' , validators = [DataRequired("How much USD do you want to start with? This must be a number.")])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class BuyForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])

class SellForm(FlaskForm):

    amount = FloatField('Amount', validators=[DataRequired()])