from flask import Blueprint, render_template

user_bp = Blueprint('user', __name__, url_prefix='/profile')


@user_bp.route('/user/', methods=['GET', 'POST'])
def profile_user():

    return render_template('/profile.html')