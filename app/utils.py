from flask import flash, redirect, request, url_for, current_app, session
from flask_login import current_user
from flask.cli import with_appcontext
import click
import requests
import os
import secrets
import time
from PIL import Image
import random
from .models import Pokemon, Team, db


BASE_API_URL = "https://pokeapi.co/api/v2/pokemon/"
response = requests.get(BASE_API_URL)
total_pokemon = response.json()["count"]
LIMIT = total_pokemon


#type chart
TYPE_EFFECTIVENESS = {
    "Normal": {"Rock": 0.5, "Ghost": 0, "Steel": 0.5},
    "Fire": {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 2, "Bug": 2, "Rock": 0.5, "Dragon": 0.5, "Steel": 2},
    "Water": {"Fire": 2, "Water": 0.5, "Grass": 0.5, "Ground": 2, "Rock": 2, "Dragon": 0.5},
    "Electric": {"Water": 2, "Electric": 0.5, "Ground": 0, "Flying": 2, "Dragon": 0.5},
    "Grass": {"Fire": 0.5, "Water": 2, "Grass": 0.5, "Poison": 0.5, "Ground": 2, "Flying": 0.5, "Bug": 0.5, "Rock": 2, "Dragon": 0.5, "Steel": 0.5},
    "Ice": {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 0.5, "Ground": 2, "Flying": 2, "Dragon": 2, "Steel": 0.5},
    "Fighting": {"Normal": 2, "Ice": 2, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Rock": 2, "Ghost": 0, "Dark": 2, "Steel": 2, "Fairy": 0.5},
    "Poison": {"Grass": 2, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0, "Fairy": 2},
    "Ground": {"Fire": 2, "Electric": 2, "Grass": 0.5, "Poison": 2, "Flying": 0, "Bug": 0.5, "Rock": 2, "Steel": 2},
    "Flying": {"Electric": 0.5, "Grass": 2, "Fighting": 2, "Bug": 2, "Rock": 0.5, "Steel": 0.5},
    "Psychic": {"Fighting": 2, "Poison": 2, "Psychic": 0.5, "Dark": 0, "Steel": 0.5},
    "Bug": {"Fire": 0.5, "Grass": 2, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2, "Ghost": 0.5, "Dark": 2, "Steel": 0.5, "Fairy": 0.5},
    "Rock": {"Fire": 2, "Ice": 2, "Fighting": 0.5, "Ground": 0.5, "Flying": 2, "Bug": 2, "Steel": 0.5},
    "Ghost": {"Normal": 0, "Psychic": 2, "Ghost": 2, "Dark": 0.5},
    "Dragon": {"Dragon": 2, "Steel": 0.5, "Fairy": 0},
    "Dark": {"Fighting": 0.5, "Psychic": 2, "Ghost": 2, "Dark": 0.5, "Fairy": 0.5},
    "Steel": {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2, "Rock": 2, "Steel": 0.5, "Fairy": 2},
    "Fairy": {"Fire": 0.5, "Fighting": 2, "Poison": 0.5, "Dragon": 2, "Dark": 2, "Steel": 0.5}
}


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

    for i in range(1, 950):
        response = requests.get(BASE_API_URL + str(i), timeout=30)
        if response.ok:
            data = response.json()
            existing_pokemon = Pokemon.query.filter_by(name=data['name']).first()
            if not existing_pokemon:
                if len(data['types']) > 1:
                    type2 = data['types'][1]['type']['name']
                else:
                    type2 = None

                pokemon = Pokemon(
                    name=data['name'],
                    main_ability=data['abilities'][0]['ability']['name'],
                    sprite_url=data['sprites']['front_default'],
                    hp_base=data['stats'][0]['base_stat'],
                    atk_base=data['stats'][1]['base_stat'],
                    def_base=data['stats'][2]['base_stat'],
                    sp_atk=data['stats'][3]['base_stat'],
                    sp_def=data['stats'][4]['base_stat'],
                    speed=data['stats'][5]['base_stat'],
                    type1=data['types'][0]['type']['name'],
                    type2=type2
                )
                db.session.add(pokemon)
                db.session.commit()
                print(f"Added {data['name']} to the database.")
                time.sleep(2)
            else:
                 print(f"{data['name']} already exists in the database.")
                 time.sleep(2)
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


def get_pokemon_for_user(user, index=0):
    """Return the first Pokémon for a user or None."""
    if user and user.team:
        pokemons = user.team.pokemons.all()
        print("Fetching Pokémon for User:", user.username, "at Index:", index)
        if index < len(pokemons):
            print("Returning Pokémon:", pokemons[index].name)
            return pokemons[index]
        else:
            print("No Pokémon found for Index:", index)
    return None


def get_total_pokemon_for_user(user):
    """Return total number of pokemon for user"""
    if user and user.team:
        return len(user.team.pokemons.all())
    return 0


def reset_battle_progress():
    session.pop('attacker_pokemon_index', None)
    session.pop('defender_pokemon_index', None)
    session.pop('attacker_score', None)
    session.pop('defender_score', None)


def type_multiplier(attacking_type, defending_type1, defending_type2=None):
    multiplier1 = TYPE_EFFECTIVENESS.get(attacking_type, {}).get(defending_type1, 1.0)
    
    if defending_type2:
        multiplier2 = TYPE_EFFECTIVENESS.get(attacking_type, {}).get(defending_type2, 1.0)
        
        # If one of the multipliers is zero, the overall effectiveness is zero.
        if multiplier1 == 0 or multiplier2 == 0:
            return 0
        return multiplier1 * multiplier2
    
    return multiplier1


def calculate_damage(attacker, defender):
    multiplier = type_multiplier(attacker.type1, defender.type1, defender.type2)
    attacking_stat = max(attacker.atk_base, attacker.sp_atk) * multiplier
    defending_stat = (max(defender.def_base, defender.sp_def) * 0.5 + min(defender.def_base, defender.sp_def) * 0.5)


    if attacking_stat < defending_stat:
        damage = random.randrange(5, 20)
    else:
        damage = max(attacking_stat - defending_stat, 1) #min damage is 1

    # Random multiplier (for instance, a value between 0.85 and 1.15)
    random_multiplier = random.uniform(0.9, 1.10)
    damage *= random_multiplier

    # Critical hit chance
    if random.uniform(0, 1) < 0.05:
        damage *= 2
        return round(damage), "Critial hit!"

    # Miss chance
    if random.uniform(0, 1) < 0.10:
        damage = 0
        return damage, f"{attacker.name} missed!"

    return round(damage), f"{attacker.name} dealt {round(damage)} damage to {defender.name}!"



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
