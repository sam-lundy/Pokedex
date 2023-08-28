from flask import Flask
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate
from .models import db, User
from flask_moment import Moment
from flask.cli import with_appcontext
from .utils import poke_db_seed
import click

# def create_app():

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY']

login_manager =  LoginManager()

db.init_app(app)

migrate = Migrate(app, db)

login_manager.init_app(app)

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'error'
login_manager.login_message = None

from app.blueprints.auth import auth
from app.blueprints.main import main
from app.blueprints.poke import poke

app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(poke)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.cli.command("seed-db")
@with_appcontext
def seed_db_command():
    """Seeds the pokemon database."""
    poke_db_seed()
    print("Database seeded!")

#Updates all users without profile pictures to have the default
@app.cli.command("update-profile-pictures")
def update_profile_pictures():
    """Ensure all users have a profile picture."""
    users_without_pictures = User.query.filter_by(profile_picture=None).all()
    for user in users_without_pictures:
        user.profile_picture = 'default_user_icon.png'

    db.session.commit()
    print("Updated profile pictures for all users.")


#resets user stats
@app.cli.command("update-user-results")
def update_user_results():
    """Ensure all users have initialized wins, losses, and draws."""
    # Fetch all users where wins, losses, or draws is None
    users_to_update = User.query.filter().all()

    # Iterate through the list of users and update their records
    for user in users_to_update:
        user.wins = 0
        user.losses = 0
        user.draws = 0
        db.session.commit()

    # Commit the changes to the database
    
    print("Updated wins, losses, and draws for all users.")


    # return app




