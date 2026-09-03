import os

import resend
from flask import current_app


def _resend_configured():
    return bool(os.getenv("RESEND_API_KEY")) and bool(os.getenv("RESEND_FROM"))


def send_email(to, subject, html):
    """Envia um email transacional via Resend.

    Nunca lança exceção: uma falha no provedor de email não deve derrubar o
    fluxo de cadastro/recuperação de senha que a chamou.
    """
    if not _resend_configured():
        current_app.logger.warning(
            "RESEND_API_KEY/RESEND_FROM não configurados; email '%s' não enviado.", subject
        )
        return None

    resend.api_key = os.getenv("RESEND_API_KEY")
    try:
        return resend.Emails.send({
            "from": f"Toodo <{os.getenv('RESEND_FROM')}>",
            "to": [to],
            "subject": subject,
            "html": html,
        })
    except Exception:
        current_app.logger.exception("Falha ao enviar email via Resend ('%s')", subject)
        return None
