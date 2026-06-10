from app import create_app
from database.conf  import banco_prod
from flask import current_app
from sqlalchemy import select, func, and_
from models.models import User,Tarefas
from datetime import datetime


from dotenv import load_dotenv
import os
from twilio.rest import Client
load_dotenv()
account_sid = os.getenv('TWILIO_ACCOUNT_SID') 
auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
client = Client(account_sid, auth_token)

app = create_app(banco_prod.DATABASE_SQLALCHEMY_URI)
with app.app_context():
        
        with current_app.Session() as session:
            stmt = (
                select(func.count(Tarefas.status), User.user, User.email)
                .filter(and_(
                    User.email.isnot(None), 
                    Tarefas.status=='pendente',
                    User.receber_mensagem == True))
                .join(Tarefas.responsavel)
                .group_by(User.id)
                
            )
            results = session.execute(stmt).all()
            print(results)