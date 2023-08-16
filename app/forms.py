from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = EmailField('Email Address: ', validators=[DataRequired()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    submit_btn = SubmitField('Sign In')

class PokemonSearchForm(FlaskForm):
    poke_search = StringField('Pokémon Name:', validators=[DataRequired()])
    poke_submit = SubmitField('Search')
                
