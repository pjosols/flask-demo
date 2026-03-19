from flask import Blueprint

laureates = Blueprint('laureates', __name__)

from app.laureates import routes
