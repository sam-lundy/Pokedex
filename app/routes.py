from flask import Flask, request, render_template, url_for, redirect
import requests
from app import app
from app.forms import LoginForm, RegisterForm, PokemonSearchForm


BASE_API_URL = "https://pokeapi.co/api/v2/pokemon/"

def get_poke_info(poke_name):
    response = requests.get(BASE_API_URL + poke_name.lower())
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
    

REGISTERED_USERS = {

}


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

        user = None

        if "@" in login_input:
            user_key = "email"
        else:
            user_key = "username"

        matching_users = [user for user, data in REGISTERED_USERS.items() if data[user_key] == login_input and data['password'] == password]

        if matching_users:
            return f"Hello, {REGISTERED_USERS[matching_users[0]]['name']}"
        else:
            return "Invalid email/username or password."
        
    return render_template('login.html', form=form)
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        name = f'{form.name.data}'
        email = form.email.data
        username = form.username.data
        password = form.password.data
        REGISTERED_USERS[email] = {
            'name': name,
            'username': username,
            'password': password
        }
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')


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
            #Converting to title in order to display in the browser
            pokemon_name = pokemon_name.title()

    return render_template('search.html', form=form, pokemon_data=pokemon_data, pokemon_name=pokemon_name, error_message=error_message)


