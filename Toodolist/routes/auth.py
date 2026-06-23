from flask import (
    Blueprint, 
    redirect, 
    render_template, 
    request, 
    current_app, 
    url_for, 
    flash,
    get_flashed_messages
)

from flask_login import (
    login_user, 
    current_user, 
    login_required,
    logout_user
)

from pwdlib import PasswordHash
from models.models import User
from sqlalchemy import select
from utils import validation_number


password_hash = PasswordHash.recommended()

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    with current_app.Session() as session:

        if request.method == 'POST':
            
            nome = request.form.get("nome")
            senha = request.form.get("senha")
            email = request.form.get("email")
            if not senha:
                flash("Digite uma senha.")
                return redirect(url_for('auth.register'))
    
            
            if not nome:
                flash("Campo de nome usuário é obrigatorio)")
                return redirect(url_for('auth.register'))
               
            elif len(nome) < 5:
                flash("Nome com menos de 5 caracteres")
                return redirect(url_for('auth.register'))
               
            elif len(senha) < 8:
                flash("Senha com menos de 8 caracteres")
                return redirect(url_for('auth.register'))

            if session.scalar(select(User).where(User.user == nome)):
                flash("Usuário já existe, tente outro nome")
                return redirect(url_for('auth.register'))
            
    
            senha_raw = password_hash.hash(senha)
            if not email:
                email = None #none em python = null em banco
            user = User(
                user = nome,
                password = senha_raw,
                email = email
            )
            print(email)

            session.add(user)
            session.commit()
            session.refresh(user)
            flash("Conta criada com sucesso")

            
            return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route('/current')
@login_required
def current():
    return render_template('current.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    
    with current_app.Session() as session:

        if request.method == 'POST':
            nome = request.form.get("nome")
            senha = request.form.get("senha")
            remember = request.form.get("remember")
            
            user = session.scalar(select(User).where(User.user == nome))
            if not user:
                flash("Usuário incorreto ou não existe")
                return redirect(url_for('auth.login'))
            
            

            if not password_hash.verify(senha, user.password):
                flash("Senha incorreta")
                return redirect(url_for('auth.login'))
            else:
                if remember == "on":
                    login_user(user, remember=True)
                else:
                    login_user(user)
                flash("Login feito com sucesso !")
                return redirect(url_for('tarefas.home'))

    return render_template('login.html')

@auth.route('/logout')
def logout():
    flash("Sessão finalizada")
    logout_user()
    return redirect(url_for('auth.login'))