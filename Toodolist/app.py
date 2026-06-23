from flask import Flask, current_app
from routes.tarefas import tarefas_bp
from routes.auth import auth
from routes.user import user_bp
from sqlalchemy import create_engine
from database.conf import Base
from sqlalchemy.orm import sessionmaker
from flask_login import LoginManager
from models.models import User
import os
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

def create_app(conf):


    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    csrf = CSRFProtect(app)
    app.register_blueprint(tarefas_bp)
    app.register_blueprint(auth)
    app.register_blueprint(user_bp)
    

    app.config["REMEMBER_COOKIE_NAME"] = "tooberemember"
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"


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
    
    return app

 