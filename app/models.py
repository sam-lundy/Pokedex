from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from flask_login import UserMixin


db = SQLAlchemy()


team_pokemon = db.Table(
    'team_pokemon',
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('pokemon_id', db.Integer, db.ForeignKey('pokemon.id'), primary_key=True)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    profile_picture = db.Column(db.String(120), nullable=True, default='default_user_icon.png')
    #Relationship
    team = db.relationship('Team', backref='user', uselist=False)

    def __init__(self, name, email, username, password):
        self.name = name
        self.email = email
        self.username = username
        self.password = generate_password_hash(password)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    #Relationship
    pokemons = db.relationship('Pokemon', secondary=team_pokemon, backref='teams', lazy='dynamic')

    def __init__(self, user_id):
        self.user_id = user_id


class Pokemon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    sprite_url = db.Column(db.String(150))
    main_ability = db.Column(db.String(50))
    base_exp = db.Column(db.Integer)
    hp_base = db.Column(db.Integer)
    atk_base = db.Column(db.Integer)
    def_base = db.Column(db.Integer)


    def __init__(self, name, sprite_url, main_ability, base_exp, hp_base, atk_base, def_base):
        self.name = name
        self.sprite_url = sprite_url
        self.main_ability = main_ability
        self.base_exp = base_exp
        self.hp_base = hp_base
        self.atk_base = atk_base
        self.def_base = def_base
