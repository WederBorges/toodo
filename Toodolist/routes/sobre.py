from flask import Blueprint, render_template
sobre_bp = Blueprint('sobre', __name__, url_prefix='/sobre')


@sobre_bp.route('/', methods=['GET'])
def sobre_page():
    return render_template('/sobre.html')