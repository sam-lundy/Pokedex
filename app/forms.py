from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo


class PokemonSearchForm(FlaskForm):
    poke_search = StringField('Pokémon Name:', validators=[DataRequired()])
    poke_submit = SubmitField('Search')

class LoginForm(FlaskForm):
    user_or_email = StringField('Username/Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])             
    email = EmailField('Email Address', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    password_conf = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')