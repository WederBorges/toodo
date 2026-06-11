from flask import current_app
from sqlalchemy import select, and_
from models.models import Tarefas, User
from app import create_app
from database.conf import banco_prod

app = create_app(banco_prod.DATABASE_SQLALCHEMY_URI)

def connection_bd():
    

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