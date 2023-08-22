from . import poke
from flask import render_template, url_for, redirect, flash, abort, session
from flask_login import current_user, login_required
from .forms import PokemonSearchForm, AddToTeamForm
from app.models import Team, Pokemon, db
from app.utils import get_poke_info, add_pokemon_to_team
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
        pokemon_data = get_poke_info(pokemon_name)
        if "error" in pokemon_data:
            error_message = pokemon_data["error"]
            pokemon_data = None
        else:
            pokemon_name = pokemon_name.title()
            session['pokemon_data'] = pokemon_data
    elif add_form.validate_on_submit():
        pokemon_name = session.get('pokemon_data', {}).get('name', '')
        add_pokemon_to_team(pokemon_name)

    return render_template('search.html', form=search_form, add_form=add_form,
                           pokemon_data=pokemon_data, pokemon_name=pokemon_name, error_message=error_message)


@poke.route('/myteam')
@login_required
def myteam():
    team = Team.query.filter_by(user_id=current_user.user_id).all()
    return render_template('myteam.html', team=team)


#Dynamically pass the integer of the poke id to the route
@poke.route('/remove_from_team/<int:pokemon_id>', methods=['POST'])
@login_required
def remove_from_team(pokemon_id):
    pokemon_to_remove = Team.query.get_or_404(pokemon_id) #Will return 404 if id doesn't exist
    if pokemon_to_remove.user_id != current_user.user_id:
        abort(403)  # Users can only remove their own pokes
    db.session.delete(pokemon_to_remove)
    db.session.commit()
    flash(f"{pokemon_to_remove.poke_name} has been removed from your team!", "success")
    return redirect(url_for('poke.myteam'))


@poke.route('/showcase', methods=['GET', 'POST'])
def showcase():
    all_pokes = Pokemon.query.all()
    random_pokes = sample(all_pokes, 10)
    add_form = AddToTeamForm()

    error_message = None
    pokemon_data = None
    
    if add_form.validate_on_submit():
        pokemon_name = add_form.pokemon_name.data
        if pokemon_name:
            add_pokemon_to_team(pokemon_name)
            
        else:
            flash("Error: Pokémon name missing.", "danger")

    return render_template('showcase.html', poke_list=random_pokes, pokemon_data=pokemon_data, add_form=add_form, error_message=error_message)
