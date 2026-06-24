from flask import Blueprint, render_template
from flask_login import current_user
landing_bp = Blueprint('landing', __name__, url_prefix='/')

@landing_bp.route('/', methods=['GET'])
def landing():
    if current_user.is_authenticated:
        return render_template('login.html')
    return render_template('landing.html')