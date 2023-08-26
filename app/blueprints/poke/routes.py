from . import poke
from flask import render_template, url_for, redirect, request, flash, abort, session
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func
from .forms import PokemonSearchForm, AddToTeamForm
from app.models import Team, Pokemon, User, Battle, db
from app.utils import add_pokemon_to_team, determine_winner, get_pokemon_for_user, reset_battle_progress
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
            session['pokemon_name'] = pokemon_name
            pokemon_data = pokemon
        else:
            error_message = f"{pokemon_name} was not found in the database."

    elif add_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to be logged in to catch Pokémon!", "danger")
            return redirect(url_for('auth.login', next=url_for('poke.search')))
        
        #If the pokemon_data isn't found in session, will default to empty dict
        pokemon_name = session.get('pokemon_name', '')
        result = add_pokemon_to_team(pokemon_name)

        if result:
            flash(f"{pokemon_name.title()} has been successfully added to your team.", "success")
            return redirect(url_for('poke.myteam'))
        

    return render_template('search.html', form=search_form, add_form=add_form, pokemon_name=pokemon_name,
                            pokemon=pokemon_data, error_message=error_message)


@poke.route('/myteam')
@login_required
def myteam():
    team = Team.query.filter_by(user_id=current_user.id).first()
    return render_template('myteam.html', team=team)


#Dynamically pass the integer of the poke id to the route
@poke.route('/remove_from_team/<int:pokemon_id>', methods=['POST'])
@login_required
def remove_from_team(pokemon_id):
    user_team_id = current_user.team.id
    user_team = Team.query.get(user_team_id)
    pokemon = Pokemon.query.get(pokemon_id)
    if not pokemon:
        flash("Pokémon not found!", "warning")
        return redirect(url_for('poke.myteam'))
    if user_team:
        user_team.pokemons.remove(pokemon)
        db.session.commit()
        flash(f"{pokemon.name} has been removed from your team!", "success")
    else:
        flash(f"{pokemon.name} not in your team!", "warning")


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



@poke.route('/battle', methods=['GET'])
@login_required
def battle_select():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('battle_select.html', users=users)


@poke.route('/battle/<int:defender_id>', methods=['POST'])
@login_required
def battle_arena(defender_id):
    attacker = current_user
    defender = User.query.get(defender_id)

    if 'attacker_score' not in session:
        session['attacker_score'] = 0
    if 'defender_score' not in session:
        session['defender_score'] = 0

    if 'attacker_pokemon_index' not in session:
        session['attacker_pokemon_index'] = 0
    if 'defender_pokemon_index' not in session:
        session['defender_pokemon_index'] = 0

    if not defender:
        flash('Invalid defender selected!', 'error')
        return redirect(url_for('poke.battle_select'))

    attacker_pokemon = get_pokemon_for_user(attacker, session.get('attacker_pokemon_index', 0))
    defender_pokemon = get_pokemon_for_user(defender, session.get('defender_pokemon_index', 0))

    if not attacker_pokemon or not defender_pokemon:
        flash('Either you or the defender does not have a Pokémon!', 'error')
        return redirect(url_for('poke.battle_select'))
    
    session['defender_id'] = defender_id

    return render_template("battle_arena.html", attacker=attacker, defender=defender, 
                           attacker_pokemon=attacker_pokemon, defender_pokemon=defender_pokemon)


@poke.route('/battle/<int:defender_id>/fight', methods=['POST'])
@login_required
def battle_fight(defender_id):
    attacker = current_user
    defender = User.query.get(defender_id)


    attacker_pokemon = get_pokemon_for_user(attacker, session['attacker_pokemon_index'])
    defender_pokemon = get_pokemon_for_user(defender, session['defender_pokemon_index'])

    outcome = determine_winner(attacker_pokemon, defender_pokemon)

    if outcome == "attacker":
        result = f"{attacker.username}'s {attacker_pokemon.name} wins!"
        session['attacker_score'] += 1
    elif outcome == "defender":
        result = f"{defender.username}'s {defender_pokemon.name} wins!"
        session['defender_score'] += 1
    else:
        result = "It's a draw!"

    new_battle = Battle(
        attacker_id=current_user.id,
        defender_id=defender_id,
        attacker_pokemon_id=attacker_pokemon.id,
        defender_pokemon_id=defender_pokemon.id,
        result=outcome
    )

    db.session.add(new_battle)
    db.session.commit()


    attacker_pokemons = current_user.team.pokemons.all() if current_user.team else []
    defender_pokemons = defender.team.pokemons.all() if defender.team else []

    if session['attacker_pokemon_index'] + 1 >= len(attacker_pokemons) or session['defender_pokemon_index'] + 1 >= len(defender_pokemons):
        return redirect(url_for('poke.battle_summary', defender_id=defender_id))

    return render_template("battle_result.html", defender=defender, result=result, attacker_score=session['attacker_score'], 
                           defender_score=session['defender_score'], defender_id=defender_id)


@poke.route('/battle/<int:defender_id>/next', methods=['POST'])
@login_required
def next_battle(defender_id):
    # Retrieve all Pokémon for both users
    attacker_pokemons = current_user.team.pokemons.all() if current_user.team else []
    defender = User.query.get(defender_id)
    defender_pokemons = defender.team.pokemons.all() if defender.team else []

    # Increment the Pokémon index
    session['attacker_pokemon_index'] += 1
    session['defender_pokemon_index'] += 1

    # Check if the battle series is over
    if session['attacker_pokemon_index'] >= len(attacker_pokemons) or session['defender_pokemon_index'] >= len(defender_pokemons):
        # Determine the overall winner and update user stats
        if session['attacker_score'] > session['defender_score']:
            current_user.wins += 1
            defender.losses += 1
            flash(f"{current_user.username} wins the battle series!", 'success')
        elif session['attacker_score'] < session['defender_score']:
            current_user.losses += 1
            defender.wins += 1
            flash(f"{defender.username} wins the battle series!", 'success')
        else:
            current_user.draws += 1
            defender.draws += 1
            flash("The battle series is a draw!", 'info')
        
        db.session.commit()
        
        # Reset battle series session variables
        reset_battle_progress()

        return redirect(url_for('poke.battle_select'))

    # Redirect to the battle arena for the next match-up
    return redirect(url_for('poke.battle_arena', defender_id=defender_id))



@poke.route('/battle/<int:defender_id>/result')
@login_required
def battle_result(defender_id):
    defender = User.query.get(defender_id)
    result = request.args.get('result')

    return render_template("battle_result.html", defender=defender, result=result)


@poke.route('/reset_battle')
@login_required
def reset_battle():
    reset_battle_progress()

    return render_template("battle_select.html")


@poke.route('/battle/<int:defender_id>/summary')
@login_required
def battle_summary(defender_id):

    attacker_id = current_user.id
    defender = User.query.get(defender_id)

    attacker_score = session.get('attacker_score', 0)
    defender_score = session.get('defender_score', 0)

    if attacker_score > defender_score:
        current_user.wins += 1
        defender.losses += 1
    elif attacker_score < defender_score:
        current_user.losses += 1
        defender.wins += 1
    else:
        current_user.draws += 1
        defender.draws += 1

    db.session.commit()

    attacker_team = current_user.team.pokemons.all() if current_user.team else []
    defender_team = defender.team.pokemons.all() if defender.team else []

    summary = f"Battle results: {current_user.username} ({current_user.wins}) vs {defender.username} ({defender.wins})"

    reset_battle_progress()

    return render_template("battle_summary.html", summary=summary, attacker_wins=attacker_score, defender_wins=defender_score,
                            attacker_team=attacker_team, defender_team=defender_team, defender=defender, attacker_id=attacker_id)


