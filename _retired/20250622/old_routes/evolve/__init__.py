from flask import Blueprint

evolve_bp = Blueprint('evolve', __name__, url_prefix='/evolve')

from . import routes 