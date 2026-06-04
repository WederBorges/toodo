from app import create_app
from database.conf import banco_prod
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from dotenv import load_dotenv
import os
from twilio.rest import Client
from sqlalchemy import select, func, and_
from models.models import User,Tarefas

load_dotenv()
account_sid = os.getenv('TWILIO_ACCOUNT_SID') 
auth_token = os.getenv('TWILIO_AUTH_TOKEN') 


app = create_app(banco_prod.DATABASE_SQLALCHEMY_URI)

def enviar_mensagem():
    with app.app_context():
        client = Client(account_sid, auth_token)
        with current_app.Session() as session:
            stmt = (
                select(func.count(Tarefas.status), User.user, User.telefone)
                .filter(and_(User.telefone.isnot(None), Tarefas.status=='pendente'))
                .join(Tarefas.responsavel)
                .group_by(User.id)
                
            )
            results = session.execute(stmt).all()


    for n in results:
        qtd = n[0]
        nome = n[1]
        tel = n[2]

        if not tel:
            continue

        tel_formatado = tel.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        print(f"Enviando para: {tel_formatado}")  # ← adiciona isso
        
        body = f"Olá, {nome}. Você tem {qtd} tarefas pendentes"
        try:
            message = client.messages.create(
                to=tel_formatado,
                from_='+18777804236',
                body=body
            )
            print(f"Enviado: {message.sid}")
        except Exception as e:
            print(f"Erro: {e}")
if __name__ == '__main__':

    scheduler = BackgroundScheduler()

    job = scheduler.add_job(enviar_mensagem, 'interval',  minutes=1)
    scheduler.start() 


    app.run(debug=True)

