from flask import Blueprint, render_template, request, url_for, redirect, flash, abort
from datetime import datetime
from flask import current_app
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from models.models import Tarefas, User
from flask_login import current_user, login_required


tarefas_bp = Blueprint('tarefas', __name__, url_prefix='/')


@tarefas_bp.route('/', methods=['GET', 'POST'])
@login_required
def home():

    
    with current_app.Session() as session:

        
        filtro = request.args.get("filtro")
        query = (select(Tarefas)).where(Tarefas.responsavel_id == current_user.id).order_by(Tarefas.status.desc())
        database = session.scalars(query).all()
        print(database)
        total_tarefas = len(database)
        
        pendente = len(session.scalars(
            select(Tarefas)
            .where(and_(
                Tarefas.status=="pendente", 
                Tarefas.responsavel_id == current_user.id))).all())
        
        concluida = len(session.scalars(
            select(Tarefas)
            .where(and_(
                Tarefas.status=="concluido", 
                Tarefas.responsavel_id == current_user.id))).all())
        
        percent = concluida/total_tarefas if database else 0
        agora = datetime.now()

        if filtro == 'all':
            database

        elif filtro == 'concluidas':
            database = session.scalars(
                select(Tarefas).
                where(and_(Tarefas.status=="concluido", Tarefas.responsavel_id == current_user.id))).all()

        elif filtro == 'pendentes':
            database = session.scalars(
                select(Tarefas).
                where(and_(Tarefas.status=="pendente", Tarefas.responsavel_id == current_user.id))).all()

        if request.method == 'POST':
            nome = request.form.get('tarefa')
            descricao = request.form.get('descricao')
            status = 'pendente'        
            
            tarefa_db = Tarefas(
                tarefa=nome,
                descricao_obj=descricao,
                status="pendente",
                created_at=agora,
                responsavel_id = current_user.id
            )

            ############### adicionar tarefa no banco ###########
            session.add(tarefa_db)
            session.commit()
            session.refresh(tarefa_db)


            return redirect(url_for('tarefas.home'))

    return render_template('index.html',
                            
                            database=database, 
                            total_tarefas=total_tarefas,
                            pendente=pendente,
                            concluida=concluida,
                            percent=f"{percent:.2%}",
                            percent_value=percent*100)


@tarefas_bp.route('/alterar-status/<int:indice>', methods=['POST'])
@login_required
def alterar_status(indice):
    
    with current_app.Session() as session:
        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == indice, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefa.home'))
        tarefa_db.status = 'concluido'
        session.commit()
        return redirect(url_for('tarefas.home'))


@tarefas_bp.route('/excluir-tarefa/<int:indice>', methods=['POST'])
@login_required
def excluir_tarefa(indice):
    
    with current_app.Session() as session:
        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == indice, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefa.home'))
        session.delete(tarefa_db)
        session.commit()
        return redirect(url_for('tarefas.home'))


@tarefas_bp.route('/editar-tarefa/<int:indice>', methods=['POST'])
@login_required
def editar_tarefa(indice):
    with current_app.Session() as session:

        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == indice, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefa.home'))
        if request.method == 'POST':
            nome = request.form.get('tarefa')
            descricao = request.form.get('descricao')
            
            tarefa_db.tarefa = nome
            tarefa_db.descricao_obj = descricao
            session.commit()
            return redirect(url_for('tarefas.home'))

