from flask import Blueprint

preview_bp = Blueprint('preview', __name__, url_prefix='/preview')

from . import routes 