from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class PokemonSearchForm(FlaskForm):
    poke_search = StringField('Pokémon Name:', validators=[DataRequired()])
    poke_submit = SubmitField('Search')


class AddToTeamForm(FlaskForm):
    add_to_team = SubmitField('Catch Pokémon')
    pokemon_name = StringField(render_kw={"type": "hidden"})