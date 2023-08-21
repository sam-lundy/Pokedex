from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, EqualTo
from .models import User


class PokemonSearchForm(FlaskForm):
    poke_search = StringField('Pokémon Name:', validators=[DataRequired()])
    poke_submit = SubmitField('Search')

class LoginForm(FlaskForm):
    user_or_email = StringField('Username/Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    name = StringField('Name', validators=[DataRequired()])             
    email = EmailField('Email Address', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    password_conf = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class AddToTeamForm(FlaskForm):
    add_to_team = SubmitField('Add to My Team')