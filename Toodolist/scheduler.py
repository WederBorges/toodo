from apscheduler.schedulers.blocking import BlockingScheduler
import os
from sqlalchemy import select, func, and_
from models.models import User,Tarefas
from services import connection_bd
import resend


def enviar_mensagem():
    
    with connection_bd() as session:
        stmt = (
                select(func.count(Tarefas.status), User.user, User.email)
                .filter(and_(
                    User.email.isnot(None), 
                    Tarefas.status=='pendente',
                    User.receber_mensagem == True))
                .join(Tarefas.responsavel)
                .group_by(User.id, User.user, User.email)
                
            )
        results = session.execute(stmt).all()
        
        resend.api_key = (os.getenv("RESEND_API_KEY"))

        for n in results:
            qtd = n[0]
            nome = n[1]
            email = n[2]

            if not email:
                continue
            
            response = resend.Emails.send({
                "from": f"Toodo <{os.getenv('RESEND_FROM')}>",
                "to": [email],
                "subject": "Lembranças do To-be",
                "html": f"<h1>Olá, {nome}. Você tem {qtd} tarefas em aberto. Não se esqueçaaa heinn!</h1>"
            })

    
scheduler = BlockingScheduler()
job = scheduler.add_job(enviar_mensagem, 'cron', hour=8, minute=30)

scheduler.start() 
