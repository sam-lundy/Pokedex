from flask import Blueprint

auth = Blueprint('auth', __name__, template_folder='auth_templates')

from . import routes