from flask import Flask, request, render_template, url_for, redirect, flash, session
from flask_login import login_user, logout_user, current_user, login_required
import requests
from app import app
from app.forms import LoginForm, RegisterForm, PokemonSearchForm
from .models import User, db
from werkzeug.security import check_password_hash
from sqlalchemy import or_


BASE_API_URL = "https://pokeapi.co/api/v2/pokemon/"

def get_poke_info(poke_name):
    response = requests.get(BASE_API_URL + poke_name.lower(), timeout=10)
    if response.ok:
        data = response.json()
        return {
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
    return render_template('myteam.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = PokemonSearchForm()
    error_message = None
    pokemon_data = None
    pokemon_name = None

    if form.validate_on_submit():
        pokemon_name = form.poke_search.data.lower()
        pokemon_data = get_poke_info(pokemon_name)

        if "error" in pokemon_data:
            error_message = pokemon_data["error"]
            pokemon_data = None
        else:
            pokemon_name = pokemon_name.title()

    return render_template('search.html', form=form, pokemon_data=pokemon_data, pokemon_name=pokemon_name, error_message=error_message)


