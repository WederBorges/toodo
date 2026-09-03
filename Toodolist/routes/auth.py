import re
from datetime import datetime

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
from models.models import User, EmailToken
from sqlalchemy import select
from extensions import limiter
from mail import send_email
from tokens import (
    generate_raw_token,
    hash_token,
    PURPOSE_VERIFY_EMAIL,
    PURPOSE_RESET_PASSWORD,
    VERIFY_EMAIL_TTL,
    RESET_PASSWORD_TTL,
)


password_hash = PasswordHash.recommended()

auth = Blueprint('auth', __name__, url_prefix='/auth')

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _create_token(session, user, purpose, ttl):
    raw_token = generate_raw_token()
    token = EmailToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        purpose=purpose,
        expires_at=datetime.now() + ttl,
    )
    session.add(token)
    session.commit()
    return raw_token


def _find_valid_token(session, raw_token, purpose):
    token = session.scalar(
        select(EmailToken).where(
            EmailToken.token_hash == hash_token(raw_token),
            EmailToken.purpose == purpose,
        )
    )
    if not token or token.used_at is not None or token.expires_at < datetime.now():
        return None
    return token


def _send_verification_email(user, raw_token):
    verify_url = url_for('auth.verify_email', token=raw_token, _external=True)
    html = render_template('email/verify_email.html', usuario=user, verify_url=verify_url)
    send_email(user.email, "Confirme seu email — To-be list", html)


def _send_reset_email(user, raw_token):
    reset_url = url_for('auth.reset_password', token=raw_token, _external=True)
    html = render_template('email/reset_password.html', usuario=user, reset_url=reset_url)
    send_email(user.email, "Redefinição de senha — To-be list", html)


@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute;30 per hour")
def register():
    with current_app.Session() as session:

        if request.method == 'POST':

            nome = request.form.get("nome")
            senha = request.form.get("senha")
            email = (request.form.get("email") or "").strip()

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

            if not email or not EMAIL_REGEX.match(email):
                flash("Digite um email válido.")
                return redirect(url_for('auth.register'))

            if session.scalar(select(User).where(User.user == nome)):
                flash("Usuário já existe, tente outro nome")
                return redirect(url_for('auth.register'))

            if session.scalar(select(User).where(User.email == email)):
                flash("Já existe uma conta com esse email")
                return redirect(url_for('auth.register'))

            senha_raw = password_hash.hash(senha)
            user = User(
                user=nome,
                password=senha_raw,
                email=email,
                email_verified=False,
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            raw_token = _create_token(session, user, PURPOSE_VERIFY_EMAIL, VERIFY_EMAIL_TTL)
            _send_verification_email(user, raw_token)

            flash("Conta criada! Verifique seu email para confirmar antes de entrar.")

            return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth.route('/verify-email/<token>')
def verify_email(token):
    with current_app.Session() as session:
        token_row = _find_valid_token(session, token, PURPOSE_VERIFY_EMAIL)
        if not token_row:
            flash("Link de confirmação inválido ou expirado. Solicite um novo.")
            return redirect(url_for('auth.resend_verification'))

        user = session.get(User, token_row.user_id)
        user.email_verified = True
        token_row.used_at = datetime.now()
        session.commit()

        flash("Email confirmado com sucesso! Você já pode entrar.")
        return redirect(url_for('auth.login'))


@auth.route('/resend-verification', methods=['GET', 'POST'])
@limiter.limit("5 per minute;20 per hour")
def resend_verification():
    if request.method == 'POST':
        email = (request.form.get("email") or "").strip()

        with current_app.Session() as session:
            user = session.scalar(select(User).where(User.email == email)) if email else None
            if user and not user.email_verified:
                raw_token = _create_token(session, user, PURPOSE_VERIFY_EMAIL, VERIFY_EMAIL_TTL)
                _send_verification_email(user, raw_token)

        # Mensagem genérica independente do resultado: evita confirmar por
        # essa via se um email está ou não cadastrado.
        flash("Se esse email existir e ainda não estiver confirmado, enviamos um novo link.")
        return redirect(url_for('auth.login'))

    return render_template('resend_verification.html')


@auth.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute;20 per hour")
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get("email") or "").strip()

        with current_app.Session() as session:
            user = session.scalar(select(User).where(User.email == email)) if email else None
            if user:
                raw_token = _create_token(session, user, PURPOSE_RESET_PASSWORD, RESET_PASSWORD_TTL)
                _send_reset_email(user, raw_token)

        # Mesma mensagem exista ou não o email: evita enumeração de contas.
        flash("Se esse email existir em nossa base, enviamos um link de redefinição de senha.")
        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def reset_password(token):
    with current_app.Session() as session:
        token_row = _find_valid_token(session, token, PURPOSE_RESET_PASSWORD)
        if not token_row:
            flash("Link de redefinição inválido ou expirado. Solicite um novo.")
            return redirect(url_for('auth.forgot_password'))

        if request.method == 'POST':
            senha = request.form.get("senha")
            senha_confirm = request.form.get("senha_confirm")

            if not senha or len(senha) < 8:
                flash("Senha com menos de 8 caracteres")
                return redirect(url_for('auth.reset_password', token=token))

            if senha != senha_confirm:
                flash("Senhas divergentes !")
                return redirect(url_for('auth.reset_password', token=token))

            user = session.get(User, token_row.user_id)
            user.password = password_hash.hash(senha)
            token_row.used_at = datetime.now()
            session.commit()

            flash("Senha redefinida com sucesso! Faça login com a nova senha.")
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute;100 per hour")
def login():

    with current_app.Session() as session:

        if request.method == 'POST':
            nome = request.form.get("nome")
            senha = request.form.get("senha")
            remember = request.form.get("remember")

            user = session.scalar(select(User).where(User.user == nome))
            # Mensagem genérica em ambos os casos: evita enumeração de
            # usuários existentes por diferença na resposta de erro.
            if not user or not senha or not password_hash.verify(senha, user.password):
                flash("Usuário ou senha incorretos")
                return redirect(url_for('auth.login'))

            if not user.email_verified:
                flash("Confirme seu email antes de entrar. Verifique sua caixa de entrada (e o spam).")
                return redirect(url_for('auth.login'))

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
