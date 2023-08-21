from flask import Flask, request, render_template, url_for, redirect, flash, abort, session
from flask_login import login_user, logout_user, current_user, login_required
from app import app
from app.forms import LoginForm, RegisterForm, PokemonSearchForm, AddToTeamForm
from .models import User, Team, db
from werkzeug.security import check_password_hash
from sqlalchemy import or_
from .utils import get_poke_info

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

#If user navigates to /home, will redirect to root
@app.route('/home')
def home_redirect():
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        login_input = form.user_or_email.data.strip().lower()
        password = form.password.data

        #using the or_ feature of sqlalchemy, can query based on email or username
        queried_user = User.query.filter(or_(User.email == login_input, User.username == login_input)).first()

        if queried_user and check_password_hash(queried_user.password, password):
            login_user(queried_user)
            flash(f"{queried_user.username} logged in.", "success")

            #redirects to the page user was on before login, if exists
            next_page = request.args.get('next', url_for('home'))
            return redirect(next_page)
        
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
        email = form.email.data.strip().lower()
        username = form.username.data.strip().lower()
        password = form.password.data

        #first() stops matching at first result
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

            #Error handling
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
        #Check if user logged in
        if not current_user.is_authenticated:
            flash("You need to be signed in to add Pokémon to your team!", "danger")
            #Saves search result to redirect after logging in
            return redirect(url_for('login', next=request.url))
        
        #If data not found, defaults to empty dict
        pokemon_data = session.get('pokemon_data', {})
        #If data found, retireves value for name otherwise empty string if name not present
        #If data not found, sets to None
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

                #Captures database errors and display it as feedback
                except Exception as e:
                    flash(f"Error adding Pokémon to your team: {str(e)}", "danger")
            else:
                flash("You already have 6 Pokémon in your team!", "warning")

    return render_template('search.html', form=form, add_form=add_form,
                           pokemon_data=pokemon_data, pokemon_name=pokemon_name, error_message=error_message)


#Dynamically pass the integer of the poke id to the route
@app.route('/remove_from_team/<int:pokemon_id>', methods=['POST'])
@login_required
def remove_from_team(pokemon_id):
    pokemon_to_remove = Team.query.get_or_404(pokemon_id) #Will return 404 if id doesn't exist
    if pokemon_to_remove.user_id != current_user.user_id:
        abort(403)  # Users can only remove their own pokes
    db.session.delete(pokemon_to_remove)
    db.session.commit()
    flash(f"{pokemon_to_remove.poke_name} has been removed from your team!", "success")
    return redirect(url_for('myteam'))
