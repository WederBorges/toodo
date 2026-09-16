from flask import Blueprint, render_template, request, url_for, redirect, flash, abort
from datetime import datetime
from flask import current_app
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, and_, case, func
from models.models import Tarefas, Etapa, User
from flask_login import current_user, login_required


tarefas_bp = Blueprint('tarefas', __name__, url_prefix='/tarefas')

STATUS_CHOICES = [
    ("pendente", "Pendente"),
    ("em_andamento", "Em andamento"),
    ("aguardando_retorno", "Aguardando retorno"),
    ("concluido", "Concluído"),
    ("cancelado", "Cancelado"),
]
STATUS_VALIDOS = {chave for chave, _ in STATUS_CHOICES}

STATUS_FILTROS = {
    "pendentes": "pendente",
    "em_andamento": "em_andamento",
    "aguardando_retorno": "aguardando_retorno",
    "concluidas": "concluido",
    "canceladas": "cancelado",
}

STATUS_BADGES = {
    "pendente": {"label": "Pendente", "bg": "rgba(210,153,34,0.15)", "color": "#D29922"},
    "em_andamento": {"label": "Em andamento", "bg": "rgba(88,166,255,0.15)", "color": "#58A6FF"},
    "aguardando_retorno": {"label": "Aguardando retorno", "bg": "rgba(188,140,255,0.15)", "color": "#BC8CFF"},
    "concluido": {"label": "Concluído", "bg": "rgba(46,160,67,0.15)", "color": "#2EA043"},
    "cancelado": {"label": "Cancelado", "bg": "rgba(218,54,51,0.15)", "color": "#DA3633"},
}

PRIORIDADE_CHOICES = [
    ("baixa", "Baixa"),
    ("media", "Média"),
    ("alta", "Alta"),
]
PRIORIDADE_VALIDAS = {chave for chave, _ in PRIORIDADE_CHOICES}
PRIORIDADE_ORDEM = {"baixa": 1, "media": 2, "alta": 3}

PRIORIDADE_BADGES = {
    "baixa": {"label": "Baixa", "bg": "rgba(88,166,255,0.15)", "color": "#58A6FF"},
    "media": {"label": "Média", "bg": "rgba(210,153,34,0.15)", "color": "#D29922"},
    "alta": {"label": "Alta", "bg": "rgba(218,54,51,0.15)", "color": "#DA3633"},
}

PRIORIDADE_RANK = case(
    *[(Tarefas.prioridade == chave, valor) for chave, valor in PRIORIDADE_ORDEM.items()],
    else_=0,
)

ORDENACAO_VALIDAS = {"data", "prioridade"}
DIRECAO_VALIDAS = {"asc", "desc"}


@tarefas_bp.route('/', methods=['GET', 'POST'])
@login_required
def home():

    with current_app.Session() as session:

        condicoes = [Tarefas.responsavel_id == current_user.id]

        filtro = request.args.get("filtro")
        prioridade_filtro = request.args.get("prioridade")
        fixadas_filtro = request.args.get("fixadas") == "1"
        busca = request.args.get("q", "").strip()
        ordenar = request.args.get("ordenar")
        direcao = request.args.get("direcao", "desc")
        if direcao not in DIRECAO_VALIDAS:
            direcao = "desc"

        ##### Filtros #####
        # Todos os filtros abaixo são combináveis entre si: busca, status,
        # prioridade e "somente fixadas" se somam na mesma consulta.

        if busca:
            condicoes.append(Tarefas.tarefa.like(f"%{busca}%"))

        if filtro in STATUS_FILTROS:
            condicoes.append(Tarefas.status == STATUS_FILTROS[filtro])

        if prioridade_filtro in PRIORIDADE_VALIDAS:
            condicoes.append(Tarefas.prioridade == prioridade_filtro)
        else:
            prioridade_filtro = None

        if fixadas_filtro:
            condicoes.append(Tarefas.fixada.is_(True))

        ##### Contadores #####
        pendente = len(session.scalars(
            select(Tarefas)
            .where(and_(
                Tarefas.status.notin_(["concluido", "cancelado"]),
                Tarefas.responsavel_id == current_user.id))).all())

        concluida = len(session.scalars(
            select(Tarefas)
            .where(and_(
                Tarefas.status=="concluido",
                Tarefas.responsavel_id == current_user.id))).all())

        fixadas_total = len(session.scalars(
            select(Tarefas)
            .where(and_(
                Tarefas.fixada.is_(True),
                Tarefas.responsavel_id == current_user.id))).all())

        status_counts = dict(session.execute(
            select(Tarefas.status, func.count())
            .where(Tarefas.responsavel_id == current_user.id)
            .group_by(Tarefas.status)).all())
        total_geral = sum(status_counts.values())


        if ordenar == "data":
            criterio = Tarefas.created_at.asc() if direcao == "asc" else Tarefas.created_at.desc()
        elif ordenar == "prioridade":
            criterio = PRIORIDADE_RANK.asc() if direcao == "asc" else PRIORIDADE_RANK.desc()
        else:
            ordenar = None
            criterio = Tarefas.status.desc()

        query = (select(Tarefas)
                 .options(selectinload(Tarefas.etapas))
                 .where(and_(*condicoes))
                 .order_by(Tarefas.fixada.desc(), criterio))

        database = session.scalars(query).all()
        total_tarefas = len(database)
        percent = concluida/total_tarefas if database else 0
        agora = datetime.now()

        if request.method == 'POST':
            nome = request.form.get('tarefa')
            descricao = request.form.get('descricao')
            prioridade = request.form.get('prioridade')
            if prioridade not in PRIORIDADE_VALIDAS:
                prioridade = 'media'

            tarefa_db = Tarefas(
                tarefa=nome,
                descricao_obj=descricao,
                status="pendente",
                prioridade=prioridade,
                created_at=agora,
                responsavel_id = current_user.id
            )

            ############### adicionar tarefa no banco ###########
            session.add(tarefa_db)
            session.commit()
            session.refresh(tarefa_db)


            return redirect(url_for('tarefas.home', **request.args))

    return render_template('index.html',

                            database=database,
                            total_tarefas=total_tarefas,
                            pendente=pendente,
                            concluida=concluida,
                            fixadas_total=fixadas_total,
                            status_counts=status_counts,
                            total_geral=total_geral,
                            percent=f"{percent:.2%}",
                            percent_value=percent*100,
                            status_choices=STATUS_CHOICES,
                            status_badges=STATUS_BADGES,
                            prioridade_choices=PRIORIDADE_CHOICES,
                            prioridade_badges=PRIORIDADE_BADGES,
                            ordenar_atual=ordenar,
                            direcao_atual=direcao,
                            prioridade_atual=prioridade_filtro,
                            fixadas_atual=fixadas_filtro)


@tarefas_bp.route('/alterar-status/<int:indice>', methods=['POST'])
@login_required
def alterar_status(indice):

    with current_app.Session() as session:
        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == indice, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefas.home', **request.args))
        if tarefa_db.status == None or tarefa_db.status != 'concluido':
            tarefa_db.status = 'concluido'
        else:
            tarefa_db.status = 'pendente'
        session.commit()
        return redirect(url_for('tarefas.home', **request.args))


@tarefas_bp.route('/fixar-tarefa/<int:indice>', methods=['POST'])
@login_required
def fixar_tarefa(indice):

    with current_app.Session() as session:
        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == indice, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefas.home', **request.args))
        tarefa_db.fixada = not tarefa_db.fixada
        session.commit()
        return redirect(url_for('tarefas.home', **request.args))


@tarefas_bp.route('/excluir-tarefa/<int:indice>', methods=['POST'])
@login_required
def excluir_tarefa(indice):

    with current_app.Session() as session:
        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == indice, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefas.home', **request.args))
        session.delete(tarefa_db)
        session.commit()
        return redirect(url_for('tarefas.home', **request.args))


@tarefas_bp.route('/editar-tarefa/<int:indice>', methods=['POST'])
@login_required
def editar_tarefa(indice):
    with current_app.Session() as session:

        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == indice, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefas.home', **request.args))
        if request.method == 'POST':
            nome = request.form.get('tarefa')
            descricao = request.form.get('descricao')
            status = request.form.get('status')
            prioridade = request.form.get('prioridade')

            tarefa_db.tarefa = nome
            tarefa_db.descricao_obj = descricao
            if status in STATUS_VALIDOS:
                tarefa_db.status = status
            if prioridade in PRIORIDADE_VALIDAS:
                tarefa_db.prioridade = prioridade
            session.commit()
            return redirect(url_for('tarefas.home', **request.args))


@tarefas_bp.route('/adicionar-etapa/<int:tarefa_id>', methods=['POST'])
@login_required
def adicionar_etapa(tarefa_id):

    with current_app.Session() as session:
        tarefa_db = session.scalar(select(Tarefas).where(and_(Tarefas.id == tarefa_id, Tarefas.responsavel_id == current_user.id)))
        if not tarefa_db:
            flash("Tarefa inexistente")
            return redirect(url_for('tarefas.home', **request.args))

        descricao = (request.form.get('descricao') or '').strip()
        if descricao:
            etapa = Etapa(descricao=descricao, tarefa_id=tarefa_db.id)
            session.add(etapa)
            session.commit()

        return redirect(url_for('tarefas.home', **dict(request.args, open_etapas=tarefa_id)))


@tarefas_bp.route('/alternar-etapa/<int:etapa_id>', methods=['POST'])
@login_required
def alternar_etapa(etapa_id):

    with current_app.Session() as session:
        etapa = session.scalar(
            select(Etapa)
            .join(Tarefas, Etapa.tarefa_id == Tarefas.id)
            .where(and_(
                Etapa.id == etapa_id,
                Tarefas.responsavel_id == current_user.id))
        )
        if not etapa:
            flash("Etapa inexistente")
            return redirect(url_for('tarefas.home', **request.args))

        etapa.concluida = not etapa.concluida
        tarefa_id = etapa.tarefa_id
        session.commit()
        return redirect(url_for('tarefas.home', **dict(request.args, open_etapas=tarefa_id)))


@tarefas_bp.route('/excluir-etapa/<int:etapa_id>', methods=['POST'])
@login_required
def excluir_etapa(etapa_id):

    with current_app.Session() as session:
        etapa = session.scalar(
            select(Etapa)
            .join(Tarefas, Etapa.tarefa_id == Tarefas.id)
            .where(and_(
                Etapa.id == etapa_id,
                Tarefas.responsavel_id == current_user.id))
        )
        if not etapa:
            flash("Etapa inexistente")
            return redirect(url_for('tarefas.home', **request.args))

        tarefa_id = etapa.tarefa_id
        session.delete(etapa)
        session.commit()
        return redirect(url_for('tarefas.home', **dict(request.args, open_etapas=tarefa_id)))
