from flask import Blueprint, render_template, request, current_app, flash, url_for, redirect
from flask_login import current_user
from models.models import User
from sqlalchemy.orm import Session
from sqlalchemy import select
user_bp = Blueprint('user', __name__, url_prefix='/profile')


@user_bp.route('/user/', methods=['GET', 'POST'])
def profile_user():

    if request.method == 'POST':
        
        with current_app.Session() as session:

            nome_user = request.form.get("nome")
            email = request.form.get("email")
            senha = request.form.get("senha")
            senhaconfirma = request.form.get("senha_confirm")
            print(nome_user, email, senha)
            name_exists = session.scalar(select(User).where(User.user == nome_user))
            email_exists = session.scalar(select(User).where(User.email == email))
            
            us_atual = session.scalar(select(User).where(User.id == current_user.id))

            if nome_user:
                if name_exists and name_exists.user != us_atual.user:
                    flash("este nik ja existe patrão")
                else:
                    us_atual.user = nome_user
                    flash("Nome alterado com sucesso fiote.")
            if email:
                if email_exists and email_exists.email != us_atual.email:
                    flash("esse email ja isiste")
                else:
                    us_atual.email = email
                    flash("email alterado com sucesso fiote.")
                   
            session.commit()
            session.refresh(us_atual)
            return redirect(url_for('user.profile_user'))

    return render_template('/profile.html')