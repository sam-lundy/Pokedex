from flask import Flask
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate
from .models import db, User
from flask.cli import with_appcontext
import click

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY']

login_manager =  LoginManager()

db.init_app(app)

migrate = Migrate(app, db)

login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

from app import routes, models

from .utils import poke_db_seed

@app.cli.command("seed-db")
@with_appcontext
def seed_db_command():
    """Seeds the pokemon database."""
    poke_db_seed()
    print("Database seeded!")
