from app import app, db
from flask import Flask, current_app
from flask.cli import with_appcontext
import click
import requests
from .models import Pokemon, db


#Used for search functionality
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


#This seeds the pokemon table with all pokes. Should only be used on initialization
#call with 'flask seed-db
BASE_API_URL = "https://pokeapi.co/api/v2/pokemon/"

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
                    name=data['name'],
                    main_ability=data['abilities'][0]['ability']['name'],
                    base_exp=data['base_experience'],
                    sprite_url=data['sprites']['front_default'],
                    hp_base=data['stats'][0]['base_stat'],
                    atk_base=data['stats'][1]['base_stat'],
                    def_base=data['stats'][2]['base_stat']
                )
                db.session.add(pokemon)
                db.session.commit()
                print(f"Added {data['name']} to the database.")
            else:
                print(f"Error fetching data for Pokemon ID {i}. Status code: {response.status_code}") 
