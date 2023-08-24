from flask import flash, redirect, request, url_for, current_app
from flask_login import current_user
from flask.cli import with_appcontext
import click
import requests
import os
import secrets
from PIL import Image
from .models import Pokemon, Team, db


#Used for search 
BASE_API_URL = "https://pokeapi.co/api/v2/pokemon/"
response = requests.get(BASE_API_URL)
total_pokemon = response.json()["count"]
LIMIT = total_pokemon


def add_pokemon_to_team(pokemon_name):
    if not current_user.is_authenticated:
        flash("You need to be signed in to catch Pokémon!", "danger")
        return redirect(url_for('auth.login', next=request.url))
    
    #Getting poke info from DB
    pokemon = Pokemon.query.filter_by(name=pokemon_name).first()
    team = Team.query.filter_by(user_id=current_user.id).first()
    
    if not team:
        #If team is empty, create one
        team = Team(user_id=current_user.id)
        db.session.add(team)
        db.session.commit()
        
    team_count = team.pokemons.count()
    
    #Checks if poke in DB
    if not pokemon:
        flash(f"{pokemon_name.title()} does not exist in the database", "warning")
        return None

    #Checks if poke in team
    if pokemon in team.pokemons:
        flash(f"{pokemon_name.title()} is already in your team!", "warning")
        return None

    if team_count < 6:
        try:
            team.pokemons.append(pokemon)
            db.session.commit()
            flash(f"{pokemon_name.title()} added to your team!", "success")
            return True
        except Exception as e:
            flash(f"Error adding Pokémon to your team: {str(e)}", "danger")
            return None
    else:
        flash("You already have 6 Pokémon in your team!", "warning")
        return None
    

#This seeds the pokemon table with all pokes. Should only be used on initialization
#call with 'flask seed-db

def poke_db_seed():

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
                 print(f"{data['name']} already exists in the database.")
        else:
            print(f"Error fetching data for Pokemon ID {i}. Status code: {response.status_code}") 


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn



#This is a legacy function to query the API. If the Pokemon DB is seeded it is not needed.
# def get_poke_info(pokemon_name):
#     print("Fetching data for Pokémon:", pokemon_name)
#     response = requests.get(BASE_API_URL + pokemon_name.lower(), timeout=10)
    
#     if response.ok:
#         data = response.json()
#         print("API Response:", data)

#         if 'name' in data:
#             return {
#                 "name": data.get('name', ''),
#                 "main_ability": data.get('abilities', [{}])[0].get('ability', {}).get('name', ''),
#                 "base_experience": data.get('base_experience', ''),
#                 "sprite_url": data.get('sprites', {}).get('front_default', ''),
#                 "hp_base": data.get('stats', [{}])[0].get('base_stat', ''),
#                 "atk_base": data.get('stats', [{}])[1].get('base_stat', ''),
#                 "def_base": data.get('stats', [{}])[2].get('base_stat', '')
#             }
#         else:
#             error_message = f"Unexpected API response structure for {pokemon_name}."
#             print(error_message)  
#             return {"error": error_message}
#     else:
#         error_message = f"Error getting info for {pokemon_name}. Status code: {response.status_code}"
#         print(error_message)  
#         return {"error": error_message}
