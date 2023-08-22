from flask import Blueprint

poke = Blueprint('poke', __name__, template_folder="poke_templates")

from . import routes