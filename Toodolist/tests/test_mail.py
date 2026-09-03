import mail


def test_send_email_noop_when_not_configured(monkeypatch, app):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM", raising=False)

    with app.app_context():
        result = mail.send_email("dest@example.com", "Assunto", "<p>oi</p>")

    assert result is None


def test_send_email_calls_resend_when_configured(monkeypatch, app):
    monkeypatch.setenv("RESEND_API_KEY", "fake-key")
    monkeypatch.setenv("RESEND_FROM", "noreply@example.com")

    calls = []

    def fake_send(payload):
        calls.append(payload)
        return {"id": "abc"}

    monkeypatch.setattr(mail.resend.Emails, "send", staticmethod(fake_send))

    with app.app_context():
        result = mail.send_email("dest@example.com", "Assunto", "<p>oi</p>")

    assert result == {"id": "abc"}
    assert calls[0]["to"] == ["dest@example.com"]
    assert calls[0]["subject"] == "Assunto"
    assert "noreply@example.com" in calls[0]["from"]


def test_send_email_swallows_resend_errors(monkeypatch, app):
    monkeypatch.setenv("RESEND_API_KEY", "fake-key")
    monkeypatch.setenv("RESEND_FROM", "noreply@example.com")

    def boom(payload):
        raise RuntimeError("resend indisponível")

    monkeypatch.setattr(mail.resend.Emails, "send", staticmethod(boom))

    with app.app_context():
        result = mail.send_email("dest@example.com", "Assunto", "<p>oi</p>")

    assert result is None
