from flask import Flask, current_app
from routes.tarefas import tarefas_bp
from routes.auth import auth
from sqlalchemy import create_engine
from database.conf import Base
from sqlalchemy.orm import sessionmaker
from flask_login import LoginManager
from models.models import User

def create_app(conf):
    

    app = Flask(__name__)
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
    
    app.register_blueprint(tarefas_bp)
    app.register_blueprint(auth)
    
    engine = create_engine(conf)
    Session = sessionmaker(bind=engine) 
    app.Session = Session

    #Configuração flask login
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        with current_app.Session() as session:
            return session.get(User, int(user_id))
    
    return app

 