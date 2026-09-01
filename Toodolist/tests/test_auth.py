from tests.conftest import login


def test_register_creates_user_and_redirects_to_login(client):
    response = client.post(
        "/auth/register",
        data={"nome": "novousuario", "senha": "senha1234", "email": ""},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        data={"nome": "novousuario", "senha": "1234567", "email": ""},
        follow_redirects=True,
    )

    assert "Senha com menos de 8 caracteres".encode() in response.data


def test_register_rejects_short_username(client):
    response = client.post(
        "/auth/register",
        data={"nome": "ab", "senha": "senha1234", "email": ""},
        follow_redirects=True,
    )

    assert "Nome com menos de 5 caracteres".encode() in response.data


def test_register_rejects_missing_username(client):
    response = client.post(
        "/auth/register",
        data={"senha": "senha1234", "email": ""},
        follow_redirects=True,
    )

    assert "Campo de nome usuário é obrigatorio".encode() in response.data


def test_register_rejects_missing_password(client):
    response = client.post(
        "/auth/register",
        data={"nome": "novousuario", "email": ""},
        follow_redirects=True,
    )

    assert "Digite uma senha.".encode() in response.data


def test_register_rejects_duplicate_username(client, make_user):
    make_user(nome="existente", senha="senha1234")

    response = client.post(
        "/auth/register",
        data={"nome": "existente", "senha": "outrasenha1", "email": ""},
        follow_redirects=True,
    )

    assert "Usuário já existe".encode() in response.data


def test_login_success_redirects_to_home(client, make_user):
    make_user(nome="fulano", senha="senha1234")

    response = login(client, "fulano", "senha1234")

    assert response.status_code == 200
    assert "Login feito com sucesso".encode() in response.data


def test_login_wrong_password_shows_generic_message(client, make_user):
    make_user(nome="fulano", senha="senha1234")

    response = login(client, "fulano", "senhaerrada")

    assert "Usuário ou senha incorretos".encode() in response.data


def test_login_unknown_user_shows_same_generic_message(client):
    response = login(client, "naoexiste", "senhaerrada")

    assert "Usuário ou senha incorretos".encode() in response.data


def test_login_with_remember_me_sets_remember_cookie(client, make_user):
    make_user(nome="fulano", senha="senha1234")

    response = login(client, "fulano", "senha1234", remember="on")

    assert response.status_code == 200
    assert client.get_cookie("tooberemember") is not None


def test_login_missing_password_does_not_crash(client, make_user):
    make_user(nome="fulano", senha="senha1234")

    response = client.post(
        "/auth/login",
        data={"nome": "fulano"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Usuário ou senha incorretos".encode() in response.data


def test_protected_route_redirects_anonymous_user_to_login(client):
    response = client.get("/tarefas/", follow_redirects=False)

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_logout_clears_session(client, make_user):
    make_user(nome="fulano", senha="senha1234")
    login(client, "fulano", "senha1234")

    client.get("/auth/logout")
    response = client.get("/tarefas/", follow_redirects=False)

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_password_is_hashed_not_stored_in_plaintext(client, app):
    client.post(
        "/auth/register",
        data={"nome": "seguro", "senha": "senha1234", "email": ""},
    )

    from sqlalchemy import select
    from models.models import User

    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "seguro"))
        assert user.password != "senha1234"
        assert user.password.startswith("$argon2")
