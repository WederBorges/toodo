from apscheduler.schedulers.blocking import BlockingScheduler
import os
from sqlalchemy import select, func, and_
from models.models import User,Tarefas
from services import connection_bd
import resend
from flask import render_template
from datetime import datetime

def enviar_mensagem():
    resend.api_key = os.getenv("RESEND_API_KEY")

    with connection_bd() as session:
        stmt_users = (
            select(User)
            .join(Tarefas.responsavel)
            .filter(
                and_(
                    User.email.isnot(None),
                    User.receber_mensagem == True,
                    Tarefas.status == "pendente"
                )
            )
            .group_by(User.id)
        )

        usuarios = session.execute(stmt_users).scalars().all()

        for usuario in usuarios:
            tarefas_pendentes = (
                session.execute(
                    select(Tarefas)
                    .filter(
                        and_(
                            Tarefas.responsavel_id == usuario.id,
                            Tarefas.status == "pendente"
                        )
                    )
                )
                .scalars()
                .all()
            )

            if not tarefas_pendentes:
                continue

            html = render_template(
                "email/email_gazette.html",
                usuario=usuario,
                tarefas_pendentes=tarefas_pendentes,
                data_hoje=datetime.now().strftime("%d/%m/%Y"),
                edicao_num=1,
                url_app="https://www.toobe-list.com.br/",
                url_unsubscribe="https://www.toobe-list.com.br/"
            )

            response = resend.Emails.send({
                "from": f"Toodo <{os.getenv('RESEND_FROM')}>",
                "to": [usuario.email],
                "subject": "The To-be Gazette — suas tarefas pendentes",
                "html": html
            })

    
# scheduler = BlockingScheduler()
# job = scheduler.add_job(enviar_mensagem, 'cron', hour=8, minute=30)

# scheduler.start() 
if __name__ == "__main__":
    enviar_mensagem()