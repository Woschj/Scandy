from flask import Blueprint, render_template
from ..models.database import Database

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Zeigt die Startseite mit Kurzanleitung und wichtigen Hinweisen"""
    return render_template('index.html') 