from app import app, db
from flask import Flask, current_app
from flask.cli import with_appcontext
import click
import requests
from .models import Pokemon, db


#Used for search 
BASE_API_URL = "https://pokeapi.co/api/v2/pokemon/"

def get_poke_info(poke_name):
    print("Fetching data for Pokémon:", poke_name)
    response = requests.get(BASE_API_URL + poke_name.lower(), timeout=10)
    
    if response.ok:
        data = response.json()
        print("API Response:", data)

        if 'name' in data:
            return {
                "name": data.get('name', ''),
                "main_ability": data.get('abilities', [{}])[0].get('ability', {}).get('name', ''),
                "base_experience": data.get('base_experience', ''),
                "sprite_url": data.get('sprites', {}).get('front_default', ''),
                "hp_base": data.get('stats', [{}])[0].get('base_stat', ''),
                "atk_base": data.get('stats', [{}])[1].get('base_stat', ''),
                "def_base": data.get('stats', [{}])[2].get('base_stat', '')
            }
        else:
            error_message = f"Unexpected API response structure for {poke_name}."
            print(error_message)  
            return {"error": error_message}
    else:
        error_message = f"Error getting info for {poke_name}. Status code: {response.status_code}"
        print(error_message)  
        return {"error": error_message}
    


    

#This seeds the pokemon table with all pokes. Should only be used on initialization
#call with 'flask seed-db

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
