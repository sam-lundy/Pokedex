from . import poke
from flask import render_template, url_for, redirect, request, flash, abort, session, jsonify
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func
from .forms import PokemonSearchForm, AddToTeamForm
from app.models import Team, Pokemon, User, Battle, db
from app.utils import add_pokemon_to_team, get_pokemon_for_user, reset_battle_progress, calculate_damage



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
    reset_battle_progress()
    #filters out users with no pokemon on their team
    users = db.session.query(User).join(Team).filter(Team.pokemons.any(), User.id != current_user.id).all()
    return render_template('battle_select.html', users=users)


@poke.route('/battle/<int:defender_id>', methods=['GET', 'POST'])
@login_required
def battle_arena(defender_id):
    attacker = current_user
    defender = User.query.get(defender_id)

    if not defender:
        flash('Invalid defender selected!', 'error')
        return redirect(url_for('poke.battle_select'))

    attacker_pokemon = get_pokemon_for_user(attacker, session.get('attacker_pokemon_index'))
    defender_pokemon = get_pokemon_for_user(defender, session.get('defender_pokemon_index'))

    if not attacker_pokemon or not defender_pokemon:
        flash('Either you or the defender does not have a Pokémon!', 'error')
        return redirect(url_for('poke.battle_select'))
    

    session.setdefault('attacker_pokemon_index', 0)
    session.setdefault('defender_pokemon_index', 0)
    session.setdefault('attacker_score', 0)
    session.setdefault('defender_score', 0)

    session['attacker_current_hp'] = attacker_pokemon.hp_base
    session['defender_current_hp'] = defender_pokemon.hp_base

    print("Initializing Attacker HP:", session['attacker_current_hp'])
    print("Initializing Defender HP:", session['defender_current_hp'])

    print("Attacker Pokémon Index:", session['attacker_pokemon_index'])
    print("Defender Pokémon Index:", session['defender_pokemon_index'])

    print("Attacker's Pokémon:", attacker_pokemon.name)
    print("Defender's Pokémon:", defender_pokemon.name)


    session['defender_id'] = defender_id

    return render_template("battle_arena.html", attacker=attacker, defender=defender, 
                           attacker_pokemon=attacker_pokemon, defender_pokemon=defender_pokemon, defender_id=defender_id)


@poke.route('/battle/<int:defender_id>/fight', methods=['POST'])
@login_required
def battle_fight(defender_id):
    attacker = current_user
    defender = User.query.get(defender_id)

    attacker_pokemon = get_pokemon_for_user(attacker, session['attacker_pokemon_index'])
    defender_pokemon = get_pokemon_for_user(defender, session['defender_pokemon_index'])

    fast_pokemon, slow_pokemon = (attacker_pokemon, defender_pokemon) if attacker_pokemon.speed > defender_pokemon.speed else (defender_pokemon, attacker_pokemon)


    if session['attacker_current_hp'] <= 0 or session['defender_current_hp'] <= 0:
        return jsonify({
            'error': 'One of the Pokémon has already fainted.',
            'attacker_hp': max(0, session['attacker_current_hp']),
            'defender_hp': max(0, session['defender_current_hp'])
        })


    print(f"Before - Attacker HP: {session['attacker_current_hp']}, Defender HP: {session['defender_current_hp']}")

    print("Session Attacker HP before fight:", session['attacker_current_hp'])
    print("Session Defender HP before fight:", session['defender_current_hp'])


    print("Fast Pokémon:", fast_pokemon.name)
    print("Slow Pokémon:", slow_pokemon.name)

# Fast Pokémon attacks first
    damage_to_slow, fast_message = calculate_damage(fast_pokemon, slow_pokemon)
    print(f"Damage by {fast_pokemon.name} to {slow_pokemon.name}:", damage_to_slow)
    print(fast_message)

    if fast_pokemon == attacker_pokemon:
        session['defender_current_hp'] -= damage_to_slow
        print(f"Defender's HP after {attacker_pokemon.name} attacks:", session['defender_current_hp'])
    else:
        session['attacker_current_hp'] -= damage_to_slow
        print(f"Attacker's HP after {defender_pokemon.name} attacks:", session['attacker_current_hp'])

    # Slow Pokémon retaliates if it has HP left
    if (fast_pokemon == attacker_pokemon and session['defender_current_hp'] > 0) or (fast_pokemon == defender_pokemon and session['attacker_current_hp'] > 0):
        damage_to_fast, slow_message = calculate_damage(slow_pokemon, fast_pokemon)
        print(slow_message)
        
        if fast_pokemon == attacker_pokemon:
            session['attacker_current_hp'] -= damage_to_fast
            print(f"Attacker's HP after {slow_pokemon.name} retaliates:", session['attacker_current_hp'])
        else:
            session['defender_current_hp'] -= damage_to_fast
            print(f"Defender's HP after {fast_pokemon.name} retaliates:", session['defender_current_hp'])
    else:
        damage_to_fast = 0
        slow_message = f"{slow_pokemon.name} didn't retaliate!"

    # Convert HP values to integers (in case they're float)
    session['attacker_current_hp'] = int(session['attacker_current_hp'])
    session['defender_current_hp'] = int(session['defender_current_hp'])

    # Ensure HPs do not drop below zero
    session['attacker_current_hp'] = max(0, session['attacker_current_hp'])
    session['defender_current_hp'] = max(0, session['defender_current_hp'])

    # Determine damage to "attacker" and "defender" based on who the fast Pokémon was
    damage_to_attacker = damage_to_fast if fast_pokemon == defender_pokemon else damage_to_slow
    damage_to_defender = damage_to_slow if fast_pokemon == defender_pokemon else damage_to_fast

    print("Session Attacker HP after fight:", session['attacker_current_hp'])
    print("Session Defender HP after fight:", session['defender_current_hp'])

    
    print(f"After - Attacker HP: {session['attacker_current_hp']}, Defender HP: {session['defender_current_hp']}")

    return jsonify({
        'attacker_hp': max(0, session['attacker_current_hp']),
        'defender_hp': max(0, session['defender_current_hp']),
        'damage_to_attacker': damage_to_attacker,
        'damage_to_defender': damage_to_defender,
        'fast_pokemon_message': slow_message,
        'slow_pokemon_message': fast_message
    })


@poke.route('/battle/<int:defender_id>/next_pokemon', methods=['POST'])
@login_required
def next_pokemon(defender_id):
    # Identify which player's Pokémon was defeated
    defeated_player = request.form.get('defeated_player')

    # Increment the correct Pokémon index and get the next Pokémon
    if defeated_player == 'attacker':
        session['attacker_pokemon_index'] += 1
        next_pokemon = get_pokemon_for_user(current_user, session['attacker_pokemon_index'])
    else:
        session['defender_pokemon_index'] += 1
        defender = User.query.get(defender_id)
        next_pokemon = get_pokemon_for_user(defender, session['defender_pokemon_index'])


    # If there's a next Pokémon, return its details
    if next_pokemon:
        return jsonify({
            'has_next': True,
            'name': next_pokemon.name,
            'hp_base': next_pokemon.hp_base,
            'sprite_url': next_pokemon.sprite_url,
            'type1': next_pokemon.type1,
            'type2': next_pokemon.type2
        })

    # If there's no next Pokémon, return a flag indicating that
    return jsonify({'has_next': False})


@poke.route('/battle/<int:defender_id>/next', methods=['POST'])
@login_required
def next_battle(defender_id):
    # Identify which player's Pokémon was defeated
    defeated_player = request.form.get('defeated_player')
    battle_ended = False
    defender = User.query.get(defender_id)

    # Increment the correct Pokémon index and get the next Pokémon
    if defeated_player == 'attacker':
        session['attacker_pokemon_index'] += 1
        print("Attacker Index:", session['attacker_pokemon_index'], "Total Pokémon:", len(current_user.team.pokemons.all()))
        print("Defender Index:", session['defender_pokemon_index'], "Total Pokémon:", len(defender.team.pokemons.all()))
        next_pokemon = get_pokemon_for_user(current_user, session['attacker_pokemon_index'])
        if next_pokemon:
            session['attacker_current_hp'] = next_pokemon.hp_base
        else:
            session['attacker_current_hp'] = 0

    else:
        session['defender_pokemon_index'] += 1
        print("Attacker Index:", session['attacker_pokemon_index'], "Total Pokémon:", len(current_user.team.pokemons.all()))
        print("Defender Index:", session['defender_pokemon_index'], "Total Pokémon:", len(defender.team.pokemons.all()))
        next_pokemon = get_pokemon_for_user(defender, session['defender_pokemon_index'])
        if next_pokemon:
            session['defender_current_hp'] = next_pokemon.hp_base
        else:
            session['defender_current_hp'] = 0

    if defeated_player == 'attacker' and session['attacker_pokemon_index'] >= 6:
        next_pokemon = None
        session['defender_score'] += 1
    elif defeated_player == 'defender' and session['defender_pokemon_index'] >= 6:
        next_pokemon = None
        session['attacker_score'] += 1


    if not next_pokemon:
        battle_ended = True
        return jsonify({'has_next': False, 'battle_ended': battle_ended})
    
    response_data = {
        'has_next': True,
        'name': next_pokemon.name,
        'hp_base': next_pokemon.hp_base,
        'sprite_url': next_pokemon.sprite_url,
        'type1': next_pokemon.type1,
        'type2': next_pokemon.type2,
        'battle_ended': battle_ended
    }
    print(battle_ended)
    return jsonify(response_data)


@poke.route('/reset_battle')
@login_required
def reset_battle():
    reset_battle_progress()

    return render_template("battle_select.html")


@poke.route('/battle/<int:defender_id>/summary')
@login_required
def battle_summary(defender_id):

    attacker = current_user
    defender = User.query.get(defender_id)

    attacker_score = session.get('attacker_score', 0)
    defender_score = session.get('defender_score', 0)

    if attacker_score > defender_score:
        result = "win"
        attacker.wins += 1
        defender.losses += 1
    elif attacker_score < defender_score:
        result = "lose"
        attacker.losses += 1
        defender.wins += 1
    else:
        result = "draw"
        attacker.draws += 1
        defender.draws += 1

    db.session.commit()

    battle = Battle(attacker_id=current_user.id, defender_id=defender_id, result=result)
    db.session.add(battle)
    db.session.commit()

    attacker_wins = attacker.get_wins()
    attacker_losses = attacker.get_losses()

    defender_wins = defender.get_wins()
    defender_losses = defender.get_losses()


    attacker_team = current_user.team.pokemons.all() if current_user.team else []
    defender_team = defender.team.pokemons.all() if defender.team else []

    summary = f"Battle results: {current_user.username} ({current_user.wins}) vs {defender.username} ({defender.wins})"

    reset_battle_progress()

    return render_template("battle_summary.html", 
                           summary=summary, 
                           attacker_wins=attacker_wins, 
                           defender_wins=defender_wins,
                           attacker_losses=attacker_losses, 
                           defender_losses=defender_losses,
                            attacker_team=attacker_team, 
                            defender_team=defender_team, 
                            defender=defender, 
                            attacker_id=attacker.id)


