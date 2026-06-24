from flask import Blueprint, render_template
from flask_login import current_user
landing_bp = Blueprint('landing', __name__, url_prefix='/')

def landing_page():
    if current_user.is_authenticated:
        return render_template('login.html')
    return render_template('landing.html')