import os
import re

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-do-not-use-in-prod")
os.environ.setdefault("FLASK_DEBUG", "false")

import pytest
from pwdlib import PasswordHash
from sqlalchemy import event

from app import create_app
from database.conf import Base
from models.models import Tarefas, User

password_hash = PasswordHash.recommended()


@pytest.fixture()
def app():
    """Fresh app + in-memory DB per test. CSRF is off by default so most
    functional tests don't need to juggle tokens; flip
    app.config["WTF_CSRF_ENABLED"] = True inside a test to exercise it.

    Rate limiting is left on the real, generous limits configured in
    app.py (Flask-Limiter caches its enabled/disabled state at init time,
    so it can't be toggled per test after the fact) — no functional test
    here comes close to tripping them, and the dedicated tests in
    test_security.py exceed them on purpose to check the 429 behavior.
    """
    flask_app = create_app("sqlite:///:memory:")
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SESSION_COOKIE_SECURE=False,
        REMEMBER_COOKIE_SECURE=False,
    )
    engine = flask_app.Session.kw["bind"]

    # SQLite não aplica FKs por padrão; habilita para exercitar o mesmo
    # comportamento de ON DELETE CASCADE usado em produção (Postgres).
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield flask_app
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    def _make(nome="usuarioteste", senha="senha1234", email=None, receber_mensagem=False):
        with app.Session() as session:
            user = User(
                user=nome,
                password=password_hash.hash(senha),
                email=email,
                receber_mensagem=receber_mensagem,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            session.expunge(user)
        return user

    return _make


@pytest.fixture()
def make_tarefa(app):
    from datetime import datetime

    def _make(responsavel_id, tarefa="Tarefa", descricao="Descricao", status="pendente"):
        with app.Session() as session:
            tarefa_db = Tarefas(
                tarefa=tarefa,
                descricao_obj=descricao,
                status=status,
                created_at=datetime.now(),
                responsavel_id=responsavel_id,
            )
            session.add(tarefa_db)
            session.commit()
            session.refresh(tarefa_db)
            session.expunge(tarefa_db)
        return tarefa_db

    return _make


@pytest.fixture()
def get_tarefas(app):
    from sqlalchemy import select

    def _get(responsavel_id):
        with app.Session() as session:
            rows = session.scalars(
                select(Tarefas).where(Tarefas.responsavel_id == responsavel_id)
            ).all()
            return [
                {
                    "id": t.id,
                    "tarefa": t.tarefa,
                    "descricao_obj": t.descricao_obj,
                    "status": t.status,
                }
                for t in rows
            ]

    return _get


def login(client, nome, senha, remember=None):
    data = {"nome": nome, "senha": senha}
    if remember is not None:
        data["remember"] = remember
    return client.post("/auth/login", data=data, follow_redirects=True)


def extract_csrf_token(html):
    match = re.search(r'const token = "([^"]+)"', html)
    assert match, "csrf token não encontrado na página renderizada"
    return match.group(1)
