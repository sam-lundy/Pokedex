from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from flask_login import UserMixin
from sqlalchemy import or_


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

    def get_wins(self):
        return Battle.query.filter_by(attacker_id=self.id, result='win').count() + \
            Battle.query.filter_by(defender_id=self.id, result='lose').count()

    def get_losses(self):
        return Battle.query.filter_by(attacker_id=self.id, result='lose').count() + \
               Battle.query.filter_by(defender_id=self.id, result='win').count()

    def get_draws(self):
        return Battle.query.filter(
            or_(
                Battle.attacker_id == self.id,
                Battle.defender_id == self.id
            ),
            Battle.result == 'draw'
        ).count()


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
    hp_base = db.Column(db.Integer)
    atk_base = db.Column(db.Integer)
    def_base = db.Column(db.Integer)
    sp_atk = db.Column(db.Integer)
    sp_def = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    type1 = db.Column(db.String(20))
    type2 = db.Column(db.String(20), nullable=True)


    def __init__(self, name, sprite_url, main_ability, hp_base, atk_base, def_base, sp_atk, sp_def, speed, type1, type2):
        self.name = name
        self.sprite_url = sprite_url
        self.main_ability = main_ability
        self.hp_base = hp_base
        self.atk_base = atk_base
        self.def_base = def_base
        self.sp_atk = sp_atk
        self.sp_def = sp_def
        self.speed = speed
        self.type1 = type1
        self.type2 = type2

class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attacker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    defender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    result = db.Column(db.String(50))
    battle_date = db.Column(db.DateTime, default=datetime.utcnow)

    attacker = db.relationship('User', back_populates='battles_attacked', foreign_keys=[attacker_id])
    defender = db.relationship('User', back_populates='battles_defended', foreign_keys=[defender_id])
