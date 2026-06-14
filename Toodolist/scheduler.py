from apscheduler.schedulers.blocking import BlockingScheduler
import os
from sqlalchemy import select, func, and_
from models.models import User,Tarefas
from email.mime.text import MIMEText
from services import connection_bd, conection_stmp


def enviar_mensagem():
    
    with connection_bd() as session:
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

    
    with conection_stmp() as server:
                
        for n in results:
            qtd = n[0]
            nome = n[1]
            email = n[2]

            if not email:
                continue
            
            sender_email = os.getenv('EMAIL_TOODO')
            receiver_email = email
            subject = "Lembrancinhas do Toodo"
            body = f"Olá {nome}. Você tem {qtd} tarefas em em aberto"

            message = MIMEText(body, 'plain')
            message['Subject'] = subject
            message['From'] = sender_email
            message['To'] = receiver_email
            print(f"Enviando para: {email}")

            server.sendmail(sender_email, receiver_email, message.as_string())
                
    
scheduler = BlockingScheduler()
print("Rodei")
job = scheduler.add_job(enviar_mensagem, 'cron', hour=8, minute=30)
scheduler.start() 
