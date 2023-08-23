from . import poke
from flask import render_template, url_for, redirect, flash, abort, session
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func
from .forms import PokemonSearchForm, AddToTeamForm
from app.models import Team, Pokemon, db
from app.utils import add_pokemon_to_team
from random import sample


#DEBUGGING SESSION

# @app.route('/set-session')
# def set_session():
#     session['test_key'] = 'test_value'
#     return "Session value set"

# @app.route('/get-session')
# def get_session():
#     return session.get('test_key', 'No value in session')


@poke.route('/search', methods=['GET', 'POST'])
def search():
    search_form = PokemonSearchForm()
    add_form = AddToTeamForm()
    
    error_message = None
    pokemon_data = None
    pokemon_name = None

    if search_form.validate_on_submit():
        pokemon_name = search_form.poke_search.data.lower()
        pokemon = Pokemon.query.filter_by(name=pokemon_name).first()

        if pokemon:
            pokemon_data = {
                "name": pokemon.name,
                "main_ability": pokemon.main_ability,
                "base_experience": pokemon.base_exp,
                "sprite_url": pokemon.sprite_url,
                "hp_base": pokemon.hp_base,
                "atk_base": pokemon.atk_base,
                "def_base": pokemon.def_base
            }
            session['pokemon_data'] = pokemon_data
        else:
            error_message = f"{pokemon_name} was not found in the database."

    elif add_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to be logged in to catch Pokémon!", "danger")
            return redirect(url_for('auth.login', next=url_for('poke.discover')))
        
        #If the pokemon_data isn't found in session, will default to empty dict
        pokemon_name = session.get('pokemon_data', {}).get('name', '')
        result = add_pokemon_to_team(pokemon_name)

        if result:
            flash(f"{pokemon_name.title()} has been successfully added to your team.", "success")
            return redirect(url_for('poke.myteam'))
        

    return render_template('search.html', form=search_form, add_form=add_form,
                           pokemon_data=pokemon_data, pokemon_name=pokemon_name, error_message=error_message)


@poke.route('/myteam')
@login_required
def myteam():
    team = Team.query.filter_by(user_id=current_user.id).first()
    return render_template('myteam.html', team=team)


#Dynamically pass the integer of the poke id to the route
@poke.route('/remove_from_team/<int:pokemon_id>', methods=['POST'])
@login_required
def remove_from_team(pokemon_id):
    pokemon_to_remove = Team.query.get_or_404(pokemon_id) #Will return 404 if id doesn't exist
    if pokemon_to_remove.user_id != current_user.user.id:
        abort(403)  # Users can only remove their own pokes
    db.session.delete(pokemon_to_remove)
    db.session.commit()
    flash(f"{pokemon_to_remove.poke_name} has been removed from your team!", "success")
    return redirect(url_for('poke.myteam'))


@poke.route('/discover', methods=['GET', 'POST'])
def discover():
    random_pokes = Pokemon.query.order_by(func.random()).limit(6).all()
    add_form = AddToTeamForm()

    error_message = None
    pokemon_data = None
    
    if add_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to be logged in to catch Pokémon!", "danger")
            return redirect(url_for('auth.login', next=url_for('poke.discover')))
        
        pokemon_name = add_form.pokemon_name.data
        if pokemon_name:
            result = add_pokemon_to_team(pokemon_name)

            if result:
                return redirect(url_for('poke.myteam'))
        else:
            flash("Error: Pokémon name missing.", "danger")

    return render_template('discover.html', poke_list=random_pokes, pokemon_data=pokemon_data, add_form=add_form, error_message=error_message)
