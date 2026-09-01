from flask import Flask, current_app
from routes.tarefas import tarefas_bp
from routes.auth import auth
from routes.sobre import sobre_bp
from routes.landing import landing_bp
from routes.user import user_bp
from sqlalchemy import create_engine
from database.conf import Base
from sqlalchemy.orm import sessionmaker
from flask_login import LoginManager
from models.models import User
import os
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from extensions import limiter
from datetime import timedelta

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')


def _secure_cookies_default():
    return os.getenv("FLASK_DEBUG", "false").strip().lower() not in ("1", "true", "yes")


def create_app(conf):

    if not SECRET_KEY:
        raise RuntimeError(
            "A variável de ambiente SECRET_KEY precisa estar definida antes de iniciar a aplicação."
        )

    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    csrf = CSRFProtect(app)
    app.register_blueprint(tarefas_bp)
    app.register_blueprint(auth)
    app.register_blueprint(user_bp)
    app.register_blueprint(sobre_bp)
    app.register_blueprint(landing_bp)

    secure_cookies = _secure_cookies_default()

    app.config["REMEMBER_COOKIE_NAME"] = "tooberemember"
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)
    app.config["REMEMBER_COOKIE_SECURE"] = secure_cookies
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

    # Cookie de sessão padrão do Flask também precisa das mesmas proteções.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = secure_cookies

    # Evita que um payload gigante derrube o worker (mitigação simples de DoS).
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 2 * 1024 * 1024))

    engine = create_engine(conf)
    Session = sessionmaker(bind=engine)
    app.Session = Session

    #Configuração flask login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        with current_app.Session() as session:
            return session.get(User, int(user_id))

    # Rate limiting global + por rota sensível (ver routes/auth.py e routes/user.py).
    # Storage em memória: adequado para um único worker (padrão do docker-compose atual).
    # Ao escalar para múltiplos workers/instâncias, defina RATE_LIMIT_STORAGE_URI
    # para um Redis compartilhado, senão cada processo terá sua própria contagem.
    app.config["RATELIMIT_DEFAULT"] = "200 per minute;2000 per hour"
    app.config["RATELIMIT_STORAGE_URI"] = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
    app.config["RATELIMIT_HEADERS_ENABLED"] = True
    limiter.init_app(app)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        if current_app.config.get("SESSION_COOKIE_SECURE", secure_cookies):
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
        return response

    return app

 