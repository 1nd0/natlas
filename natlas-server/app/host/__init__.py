from flask import Blueprint

bp = Blueprint("host", __name__)

from app.host import routes as routes
