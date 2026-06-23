from flask import Blueprint, render_template, request, current_app, flash, url_for, redirect
from flask_login import current_user, login_required, logout_user
from models.models import User
from sqlalchemy.orm import Session,selectinload
from sqlalchemy import select
from pwdlib import PasswordHash

user_bp = Blueprint('user', __name__, url_prefix='/profile')
password_hash = PasswordHash.recommended()

@user_bp.route('/user/', methods=['GET', 'POST'])
@login_required
def profile_user():

    if request.method == 'POST':
        
        with current_app.Session() as session:

            nome_user = request.form.get("nome")
            email = request.form.get("email")
            senha = request.form.get("senha")
            senhaconfirma = request.form.get("senha_confirm")
            email_enabled = request.form.get("email_enabled")
            name_exists = session.scalar(select(User).where(User.user == nome_user))
            email_exists = session.scalar(select(User).where(User.email == email))
            
            us_atual = session.scalar(select(User).where(User.id == current_user.id))

            if nome_user:
                if name_exists and name_exists.user != us_atual.user:
                    flash("Esse nome de usuário já existe !")
                else:
                    us_atual.user = nome_user
                    flash("Nome alterado com sucesso !.")
            if email:
                if email_exists and email_exists.email != us_atual.email:
                    flash("Esse email já existe !")
                else:
                    us_atual.email = email
                    flash("Email alterado com sucesso !")
            if senha and senhaconfirma:
                if senha != senhaconfirma:
                    flash("Senhas divergentes !")
                    return redirect(url_for("user.profile_user"))
                elif len(senha) < 8:
                    flash("Senha com poucos caracteres !")
                else:
                    flash("Senha alterada com sucesso !")
                    senha_raw = password_hash.hash(senha)
                    us_atual.password = senha_raw
                   
            session.commit()
            session.refresh(us_atual)
            return redirect(url_for('user.profile_user'))

    return render_template('/profile.html')

@user_bp.route('/user-enable-email', methods=['POST'])
@login_required
def enable_email():
    
    with current_app.Session() as session:
        us_atual = session.scalar(select(User).where(User.id == current_user.id))
        if request.method == 'POST':
            enable_email = request.form.get('email_enabled')
            print(enable_email)
            if enable_email == None:
                us_atual.receber_mensagem = False
                session.commit()
                flash("Você não receberá emails de notificação !")
                return redirect(url_for('user.profile_user'))
            if enable_email == 'on':
                us_atual.receber_mensagem = True
                session.commit()
                flash("Você agora receberá emails de notificação !")
                return redirect(url_for('user.profile_user'))
                
@user_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    
    with current_app.Session() as session:
        us_atual = session.scalar(select(User)
                                  .options(selectinload(User.tarefas))
                                  .where(User.id == current_user.id))
        us_atual.tarefas
        if request.method == 'POST':
            confirmacao = request.form.get("confirmacao")
            if confirmacao == "EXCLUIR":
                logout_user()
                session.delete(us_atual)
                session.commit()
                flash("Conta deletada com sucesso !")
                return redirect(url_for('auth.register'))