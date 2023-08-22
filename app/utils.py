from flask import flash, redirect, request, url_for
from flask_login import current_user
from flask.cli import with_appcontext
import click
import requests
from .models import Pokemon, Team, db


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
    

def add_pokemon_to_team(pokemon_name):
    if not current_user.is_authenticated:
        flash("You need to be signed in to add Pokémon to your team!", "danger")
        return redirect(url_for('login', next=request.url))
    
    pokemon_data = get_poke_info(pokemon_name.lower())
    if "error" in pokemon_data:
        flash("Error retrieving Pokémon data. Please search again before adding to your team.", "danger")
        return None
    
    team_count = Team.query.filter_by(user_id=current_user.user_id).count()
    if team_count < 6:
        try:
            new_member = Team(current_user.user_id, pokemon_name.title(), pokemon_data['sprite_url'],
                              pokemon_data['main_ability'], pokemon_data['base_experience'],
                              pokemon_data['hp_base'], pokemon_data['atk_base'], pokemon_data['def_base'])
            
            print(pokemon_name)
            db.session.add(new_member)
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
