from flask import Flask, request, render_template, url_for, redirect, flash, session
from flask_login import login_user, logout_user, current_user, login_required
import requests
from app import app
from app.forms import LoginForm, RegisterForm, PokemonSearchForm, AddToTeamForm
from .models import User, Team, Pokemon, db
from werkzeug.security import check_password_hash
from sqlalchemy import or_


BASE_API_URL = "https://pokeapi.co/api/v2/pokemon/"

def get_poke_info(poke_name):
    response = requests.get(BASE_API_URL + poke_name.lower(), timeout=10)
    if response.ok:
        data = response.json()
        return {
            "name": data['name'],
            "main_ability": data['abilities'][0]['ability']['name'],
            "base_experience": data['base_experience'],
            "sprite_url": data['sprites']['front_default'],
            "hp_base": data['stats'][0]['base_stat'],
            "atk_base": data['stats'][1]['base_stat'],
            "def_base": data['stats'][2]['base_stat']
        }
    else:
        return {
            "error": f"Error getting info for {poke_name}. Status code: {response.status_code}"
        }

#SEED

def poke_db_seed():
    response = requests.get(BASE_API_URL)
    total_pokemon = response.json()["count"]

    LIMIT = total_pokemon

    for i in range(1, LIMIT + 1):
        response = requests.get(BASE_API_URL + str(i), timeout=10)
        if response.ok:
            data = response.json()
            existing_pokemon = Pokemon.query.filter_by(name=data['name']).first()
            if not existing_pokemon:
                pokemon = Pokemon(
                    main_ability=data['abilities'][0]['ability']['name'],
                    base_exp=data['base_experience'],
                    sprite_url=data['sprites']['front_default'],
                    hp_base=data['stats'][0]['base_stat'],
                    atk_base=data['stats'][1]['base_stat'],
                    def_base=data['stats'][2]['base_stat']
                )
                db.session.add(pokemon)
                print(f"Added {data['name']} to the database.")
            else:
                print(f"Error fetching data for Pokemon ID {i}. Status code: {response.status_code}")\
            

from random import shuffle

def generate_npc_team(user_team):
    user_team_exp = sum([pokemon.base_exp for pokemon in user_team])
    all_pokemon = Pokemon.query.all()
    shuffle(all_pokemon)

    npc_team = []
    npc_exp = 0

    for pokemon in all_pokemon:
        if len(npc_team) == 6:
            break

        if npc_exp + pokemon.base_exp <= user_team_exp:
            npc_team.append(pokemon)
            npc_exp += pokemon.base_exp

    return npc_team


#DEBUGGING SESSION

# @app.route('/set-session')
# def set_session():
#     session['test_key'] = 'test_value'
#     return "Session value set"

# @app.route('/get-session')
# def get_session():
#     return session.get('test_key', 'No value in session')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/home')
def home_redirect():
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        login_input = form.user_or_email.data.strip().lower()
        password = form.password.data

        queried_user = User.query.filter(or_(User.email == login_input, User.username == login_input)).first()

        if queried_user and check_password_hash(queried_user.password, password):
            login_user(queried_user)
            flash(f"{queried_user.username} logged in.", "success")
            if not Pokemon.query.first():
                poke_db_seed()
            return redirect(url_for('home'))
        else:
            flash("Invalid email/username or password.", "danger")
            return redirect(url_for('login'))
        
    return render_template('login.html', form=form)
    
    

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        name = form.name.data
        email = form.email.data.lower()
        username = form.username.data.lower()
        password = form.password.data

        existing_user_or_email = User.query.filter(
            or_(User.email == email, User.username == username)).first()

        if existing_user_or_email:
            flash("User already exists!", "danger")
            return render_template('register.html', form=form)

        if form.validate_on_submit():
            new_user = User(name, email, username, password)

            try:
                db.session.add(new_user)
                db.session.commit()

            except Exception as e:
                db.session.rollback()
                print(f"Error: {e}")
                flash("There was an error registering your account. Please try again.", "danger")
                return redirect(url_for('register'))
            
            else:
                flash(f"Thank you for registering, {new_user.username}!", "success")
                return redirect(url_for('login'))

    return render_template('register.html', form=form)



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/myteam')
@login_required
def myteam():
    team = Team.query.filter_by(user_id=current_user.user_id).all()
    return render_template('myteam.html', team=team)


@app.route('/search', methods=['GET', 'POST'])
def search():

    form = PokemonSearchForm()
    add_form = AddToTeamForm()

    error_message = None
    pokemon_data = None
    pokemon_name = None

    if "poke_submit" in request.form and form.validate_on_submit():
        pokemon_name = form.poke_search.data.lower()
        pokemon_data = get_poke_info(pokemon_name)

        if "error" in pokemon_data:
            error_message = pokemon_data["error"]
            pokemon_data = None
        else:
            pokemon_name = pokemon_name.title()
            session['pokemon_data'] = pokemon_data

    elif "add_to_team" in request.form and add_form.validate_on_submit():
        pokemon_data = session.get('pokemon_data', {})
        pokemon_name = pokemon_data.get('name', '').title() if pokemon_data else None

        if not pokemon_data or "error" in pokemon_data:
            flash("Error retrieving Pokémon data. Please search again before adding to your team.", "danger")
        else:
            team_count = Team.query.filter_by(user_id=current_user.user_id).count()
            if team_count < 6:
                try:
                    new_member = Team(current_user.user_id, pokemon_name, pokemon_data['sprite_url'],
                                      pokemon_data['main_ability'], pokemon_data['base_experience'],
                                      pokemon_data['hp_base'], pokemon_data['atk_base'], pokemon_data['def_base'])
                    db.session.add(new_member)
                    db.session.commit()
                    flash(f"{pokemon_name} added to your team!", "success")
                except Exception as e:
                    # This will capture any database error and display it as feedback
                    flash(f"Error adding Pokémon to your team: {str(e)}", "danger")
            else:
                flash("You already have 6 Pokémon in your team!", "warning")

    return render_template('search.html', form=form, add_form=add_form,
                           pokemon_data=pokemon_data, pokemon_name=pokemon_name, error_message=error_message)

@app.route('/remove_from_team/<int:pokemon_id>', methods=['POST'])
@login_required
def remove_from_team(pokemon_id):
    pokemon_to_remove = Team.query.get_or_404(pokemon_id)
    if pokemon_to_remove.user_id != current_user.user_id:
        abort(403)  # Forbidden access
    db.session.delete(pokemon_to_remove)
    db.session.commit()
    flash(f"{pokemon_to_remove.poke_name} has been removed from your team!", "success")
    return redirect(url_for('myteam'))


@app.route('/trainer-team', methods=['GET'])
@login_required
def trainer_team():
    user_team = Team.query.filter_by(user_id=current_user.user_id).all()
    npc_team = generate_npc_team(user_team)

    for pokemon in npc_team:
        npc_member = NPC(user_id=current_user.id, pokemon_name=pokemon.name,
                         sprite_url=pokemon.sprite_url, main_ability=pokemon.main_ability,
                         base_exp=pokemon.base_exp)
        db.session.add(npc_member)

    db.session.commit()

    return redirect(url_for('battle'))