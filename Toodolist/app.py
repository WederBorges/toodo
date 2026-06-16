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



load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY_')

def create_app(conf):
    

    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    
    app.register_blueprint(tarefas_bp)
    app.register_blueprint(auth)
    app.register_blueprint(user_bp)
    
    engine = create_engine(conf)
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(engine)
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

 