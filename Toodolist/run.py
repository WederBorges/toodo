from app import create_app
from database.conf import banco_prod
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from dotenv import load_dotenv
import os
from sqlalchemy import select, func, and_
from models.models import User,Tarefas

from smtplib import SMTP
from email.mime.text import MIMEText
load_dotenv()

SMTP_SERVER = "smtp.gmail.com"  # Replace with your SMTP server
SMTP_PORT = 587  # Use 465 for SSL or 587 for TLS
USERNAME = os.getenv('EMAIL_TOODO')  # Your email login
PASSWORD = os.getenv('PASSWORD_TOODO') # Your email password



app = create_app(banco_prod.DATABASE_SQLALCHEMY_URI)

def enviar_mensagem():

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

    with SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    
        server.starttls()
        server.login(USERNAME, PASSWORD)
            
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
                
        
        


if __name__ == '__main__':

    scheduler = BackgroundScheduler()

    job = scheduler.add_job(enviar_mensagem, 'cron', hour=8 ,minute=30)
    scheduler.start() 


    app.run(debug=True)

