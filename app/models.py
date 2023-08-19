from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    
    def get_id(self):
        return str(self.user_id)

    def __init__(self, name, email, username, password):
        self.name = name
        self.email = email
        self.username = username
        self.password = generate_password_hash(password)

class Team(db.Model, UserMixin):
    poke_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    poke_name = db.Column(db.String(50), nullable=False)
    sprite_url = db.Column(db.String(200))
    main_ability = db.Column(db.String(50))
    base_experience = db.Column(db.Integer)
    hp_base = db.Column(db.Integer)
    atk_base = db.Column(db.Integer)
    def_base = db.Column(db.Integer)

    def __init__(self, user_id, poke_name, sprite_url, main_ability, base_exp, hp_base, atk_base, def_base):
        self.user_id = user_id
        self.poke_name = poke_name
        self.sprite_url = sprite_url
        self.main_ability = main_ability
        self.base_exp = base_exp
        self.hp_base = hp_base
        self.atk_base = atk_base
        self.def_base = def_base