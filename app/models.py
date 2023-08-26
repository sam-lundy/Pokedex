from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
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
    bio = db.Column(db.String(500))
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    #Relationship
    team = db.relationship('Team', backref='user', uselist=False)
    battles_attacked = db.relationship('Battle', back_populates='attacker', foreign_keys='Battle.attacker_id')
    battles_defended = db.relationship('Battle', back_populates='defender', foreign_keys='Battle.defender_id')

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

class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attacker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    defender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    attacker_pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    defender_pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    result = db.Column(db.String(50))
    battle_date = db.Column(db.DateTime, default=datetime.utcnow)

    attacker = db.relationship('User', back_populates='battles_attacked', foreign_keys=[attacker_id])
    defender = db.relationship('User', back_populates='battles_defended', foreign_keys=[defender_id])
    attacker_pokemon = db.relationship('Pokemon', foreign_keys=[attacker_pokemon_id])
    defender_pokemon = db.relationship('Pokemon', foreign_keys=[defender_pokemon_id])
