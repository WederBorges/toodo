from sqlalchemy import select

from models.models import EmailToken, User
from tests.conftest import extract_link, extract_token_from_url, login


def test_register_sends_verification_email(client, app, sent_emails):
    client.post(
        "/auth/register",
        data={"nome": "novousuario", "senha": "senha1234", "email": "novo@example.com"},
    )

    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "novo@example.com"
    assert "Confirme seu email" in sent_emails[0]["subject"]

    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "novousuario"))
        token = session.scalar(select(EmailToken).where(EmailToken.user_id == user.id))
        assert token is not None
        assert token.purpose == "verify_email"
        assert token.used_at is None


def test_verify_email_with_valid_token_activates_account(client, app, sent_emails):
    client.post(
        "/auth/register",
        data={"nome": "novousuario", "senha": "senha1234", "email": "novo@example.com"},
    )
    link = extract_link(sent_emails[0]["html"])
    token = extract_token_from_url(link)

    response = client.get(f"/auth/verify-email/{token}", follow_redirects=True)

    assert "Email confirmado com sucesso".encode() in response.data

    with app.Session() as session:
        user = session.scalar(select(User).where(User.user == "novousuario"))
        assert user.email_verified is True

    login_response = login(client, "novousuario", "senha1234")
    assert "Login feito com sucesso".encode() in login_response.data


def test_verify_email_with_invalid_token_shows_generic_error(client):
    response = client.get("/auth/verify-email/token-invalido", follow_redirects=True)

    assert "Link de confirmação inválido ou expirado".encode() in response.data


def test_verify_email_token_is_single_use(client, sent_emails):
    client.post(
        "/auth/register",
        data={"nome": "novousuario", "senha": "senha1234", "email": "novo@example.com"},
    )
    link = extract_link(sent_emails[0]["html"])
    token = extract_token_from_url(link)

    client.get(f"/auth/verify-email/{token}")
    response = client.get(f"/auth/verify-email/{token}", follow_redirects=True)

    assert "Link de confirmação inválido ou expirado".encode() in response.data


def test_resend_verification_sends_new_token_for_unverified_user(client, make_user, sent_emails):
    make_user(nome="fulano", senha="senha1234", email="fulano@example.com", email_verified=False)

    response = client.post(
        "/auth/resend-verification",
        data={"email": "fulano@example.com"},
        follow_redirects=True,
    )

    assert len(sent_emails) == 1
    assert "novo link".encode() in response.data


def test_resend_verification_does_not_leak_unknown_email(client, sent_emails):
    response = client.post(
        "/auth/resend-verification",
        data={"email": "naoexiste@example.com"},
        follow_redirects=True,
    )

    assert len(sent_emails) == 0
    assert "novo link".encode() in response.data


def test_resend_verification_does_not_resend_for_already_verified_user(client, make_user, sent_emails):
    make_user(nome="fulano", senha="senha1234", email="fulano@example.com", email_verified=True)

    client.post(
        "/auth/resend-verification",
        data={"email": "fulano@example.com"},
        follow_redirects=True,
    )

    assert len(sent_emails) == 0


def test_forgot_password_sends_reset_email_for_known_user(client, make_user, sent_emails):
    make_user(nome="fulano", senha="senha1234", email="fulano@example.com")

    response = client.post(
        "/auth/forgot-password",
        data={"email": "fulano@example.com"},
        follow_redirects=True,
    )

    assert len(sent_emails) == 1
    assert "Redefinição de senha" in sent_emails[0]["subject"]
    assert "link de redefinição".encode() in response.data


def test_forgot_password_does_not_leak_unknown_email(client, sent_emails):
    response = client.post(
        "/auth/forgot-password",
        data={"email": "naoexiste@example.com"},
        follow_redirects=True,
    )

    assert len(sent_emails) == 0
    assert "link de redefinição".encode() in response.data


def test_reset_password_with_valid_token_changes_password(client, make_user, sent_emails):
    make_user(nome="fulano", senha="senhaAntiga1", email="fulano@example.com")

    client.post("/auth/forgot-password", data={"email": "fulano@example.com"})
    link = extract_link(sent_emails[0]["html"])
    token = extract_token_from_url(link)

    response = client.post(
        f"/auth/reset-password/{token}",
        data={"senha": "senhaNova123", "senha_confirm": "senhaNova123"},
        follow_redirects=True,
    )

    assert "Senha redefinida com sucesso".encode() in response.data

    old_login = login(client, "fulano", "senhaAntiga1")
    assert "Usuário ou senha incorretos".encode() in old_login.data

    new_login = login(client, "fulano", "senhaNova123")
    assert "Login feito com sucesso".encode() in new_login.data


def test_reset_password_rejects_mismatched_confirmation(client, make_user, sent_emails):
    make_user(nome="fulano", senha="senhaAntiga1", email="fulano@example.com")
    client.post("/auth/forgot-password", data={"email": "fulano@example.com"})
    token = extract_token_from_url(extract_link(sent_emails[0]["html"]))

    response = client.post(
        f"/auth/reset-password/{token}",
        data={"senha": "senhaNova123", "senha_confirm": "diferente"},
        follow_redirects=True,
    )

    assert "Senhas divergentes".encode() in response.data


def test_reset_password_rejects_short_password(client, make_user, sent_emails):
    make_user(nome="fulano", senha="senhaAntiga1", email="fulano@example.com")
    client.post("/auth/forgot-password", data={"email": "fulano@example.com"})
    token = extract_token_from_url(extract_link(sent_emails[0]["html"]))

    response = client.post(
        f"/auth/reset-password/{token}",
        data={"senha": "curta", "senha_confirm": "curta"},
        follow_redirects=True,
    )

    assert "Senha com menos de 8 caracteres".encode() in response.data


def test_reset_password_token_is_single_use(client, make_user, sent_emails):
    make_user(nome="fulano", senha="senhaAntiga1", email="fulano@example.com")
    client.post("/auth/forgot-password", data={"email": "fulano@example.com"})
    token = extract_token_from_url(extract_link(sent_emails[0]["html"]))

    client.post(
        f"/auth/reset-password/{token}",
        data={"senha": "senhaNova123", "senha_confirm": "senhaNova123"},
    )
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"senha": "outraSenha123", "senha_confirm": "outraSenha123"},
        follow_redirects=True,
    )

    assert "Link de redefinição inválido ou expirado".encode() in response.data


def test_reset_password_invalid_token_redirects_to_forgot_password(client):
    response = client.get("/auth/reset-password/token-invalido", follow_redirects=True)

    assert "Link de redefinição inválido ou expirado".encode() in response.data


def test_forgot_password_rate_limit_blocks_after_threshold(client):
    statuses = []
    for _ in range(10):
        response = client.post("/auth/forgot-password", data={"email": "x@example.com"})
        statuses.append(response.status_code)

    assert 429 in statuses
