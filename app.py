from flask import Flask, request, render_template, url_for, jsonify, redirect
import requests

app = Flask(__name__)

BASE_URL = "https://pokeapi.co/api/v2/pokemon/"

def get_poke_info(poke_name):
    response = requests.get(BASE_URL + poke_name.lower())
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
    
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/home')
def home_redirect():
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    pokemon_data = None
    pokemon_name = None

    if request.method == 'POST':
        pokemon_name = request.form.get('pokemon')
        if pokemon_name:
            pokemon_name = pokemon_name.lower()
            pokemon_data = get_poke_info(pokemon_name)

            #Finally converting to title in order to display in the browser
            pokemon_name = pokemon_name.title()

    return render_template('search.html', pokemon_data=pokemon_data, pokemon_name=pokemon_name)


