from sqlalchemy import select

from models.models import Tarefas, User
from tests.conftest import login


def test_profile_requires_login(client):
    response = client.get("/profile/user/", follow_redirects=False)
    assert response.status_code == 302


def test_update_username(client, make_user, app):
    make_user(nome="antigo", senha="senha1234")
    login(client, "antigo", "senha1234")

    client.post("/profile/user/", data={"nome": "novo_nome"})

    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "novo_nome"))
        assert user is not None


def test_cannot_rename_to_existing_username(client, make_user):
    make_user(nome="ocupado", senha="senha1234")
    make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    response = client.post("/profile/user/", data={"nome": "ocupado"}, follow_redirects=True)

    assert "Esse nome de usuário já existe".encode() in response.data


def test_update_email(client, make_user, app):
    make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    client.post("/profile/user/", data={"email": "novo@example.com"})

    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "dono"))
        assert user.email == "novo@example.com"


def test_cannot_use_existing_email(client, make_user):
    make_user(nome="outro", senha="senha1234", email="ocupado@example.com")
    make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    response = client.post(
        "/profile/user/", data={"email": "ocupado@example.com"}, follow_redirects=True
    )

    assert "Esse email já existe".encode() in response.data


def test_password_change_requires_matching_confirmation(client, make_user):
    make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    response = client.post(
        "/profile/user/",
        data={"senha": "novaSenha1", "senha_confirm": "diferente"},
        follow_redirects=True,
    )

    assert "Senhas divergentes".encode() in response.data


def test_password_change_rejects_short_password(client, make_user):
    make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    response = client.post(
        "/profile/user/",
        data={"senha": "abc123", "senha_confirm": "abc123"},
        follow_redirects=True,
    )

    assert "Senha com poucos caracteres".encode() in response.data


def test_password_change_updates_hash(client, make_user, app):
    from pwdlib import PasswordHash

    make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    client.post(
        "/profile/user/",
        data={"senha": "novaSenhaForte1", "senha_confirm": "novaSenhaForte1"},
    )

    password_hash = PasswordHash.recommended()
    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "dono"))
        assert password_hash.verify("novaSenhaForte1", user.password)


def test_enable_email_notifications(client, make_user, app):
    make_user(nome="dono", senha="senha1234", email="dono@example.com")
    login(client, "dono", "senha1234")

    client.post("/profile/user-enable-email", data={"email_enabled": "on"})

    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "dono"))
        assert user.receber_mensagem is True


def test_disable_email_notifications(client, make_user, app):
    make_user(nome="dono", senha="senha1234", email="dono@example.com", receber_mensagem=True)
    login(client, "dono", "senha1234")

    client.post("/profile/user-enable-email", data={})

    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "dono"))
        assert user.receber_mensagem is False


def test_delete_account_requires_exact_confirmation_word(client, make_user, app):
    make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    client.post("/profile/delete-account", data={"confirmacao": "excluir"})

    with app.Session() as session:
        assert session.scalar(select(User).where(User.user == "dono")) is not None


def test_delete_account_removes_user_and_cascades_tarefas(
    client, make_user, make_tarefa, app
):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, tarefa="Sera apagada")
    login(client, "dono", "senha1234")

    client.post("/profile/delete-account", data={"confirmacao": "EXCLUIR"})

    with app.Session() as session:
        assert session.scalar(select(User).where(User.user == "dono")) is None
        assert session.get(Tarefas, tarefa.id) is None

    response = client.get("/tarefas/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
