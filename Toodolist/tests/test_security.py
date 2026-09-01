import pytest

from tests.conftest import extract_csrf_token, login


def test_security_headers_are_present(client):
    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_hsts_not_sent_when_cookies_not_secure(client):
    # A fixture roda com SESSION_COOKIE_SECURE=False (equivalente a debug local),
    # então o header HSTS não deve ser anunciado.
    response = client.get("/")
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_sent_when_cookies_secure(app, client):
    app.config["SESSION_COOKIE_SECURE"] = True
    response = client.get("/")
    assert "max-age" in response.headers["Strict-Transport-Security"]


def test_login_post_without_csrf_token_is_rejected(app, client, make_user):
    app.config["WTF_CSRF_ENABLED"] = True
    make_user(nome="fulano", senha="senha1234")

    response = client.post(
        "/auth/login",
        data={"nome": "fulano", "senha": "senha1234"},
    )

    assert response.status_code == 400


def test_login_post_with_valid_csrf_token_succeeds(app, client, make_user):
    app.config["WTF_CSRF_ENABLED"] = True
    make_user(nome="fulano", senha="senha1234")

    page = client.get("/auth/login")
    token = extract_csrf_token(page.get_data(as_text=True))

    response = client.post(
        "/auth/login",
        data={"nome": "fulano", "senha": "senha1234", "csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Login feito com sucesso".encode() in response.data


def test_login_rate_limit_blocks_after_threshold(client, make_user):
    make_user(nome="fulano", senha="senha1234")

    statuses = [login(client, "fulano", "senhaerrada").status_code for _ in range(15)]

    assert 429 in statuses


def test_register_rate_limit_blocks_after_threshold(client):
    statuses = []
    for i in range(10):
        response = client.post(
            "/auth/register",
            data={"nome": f"usuario{i}", "senha": "senha1234", "email": ""},
        )
        statuses.append(response.status_code)

    assert 429 in statuses


def test_missing_secret_key_fails_fast(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "SECRET_KEY", None)

    with pytest.raises(RuntimeError):
        app_module.create_app("sqlite:///:memory:")
