"""F-04: письма со ссылками на страницы frontend.

Сбой почтового сервера не должен ломать регистрацию или смену email:
ошибка записывается в лог, а пользователь может запросить письмо повторно.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail

from .tokens import email_verification_token, encode_uid, password_reset_token

logger = logging.getLogger(__name__)


def _link(path: str, user, token: str) -> str:
    return f"{settings.FRONTEND_URL}{path}?{urlencode({'uid': encode_uid(user), 'token': token})}"


def _send(subject: str, body: str, to: str) -> bool:
    try:
        send_mail(subject, body, None, [to])
    except Exception:
        logger.exception("Не удалось отправить письмо «%s» на %s", subject, to)
        return False
    return True


def send_verification_email(user) -> bool:
    link = _link("/verify-email", user, email_verification_token.make_token(user))
    body = (
        "Здравствуйте!\n\n"
        "Подтвердите email на платформе «Стажировки KG», перейдя по ссылке:\n"
        f"{link}\n\n"
        "Если вы не регистрировались, просто проигнорируйте это письмо."
    )
    return _send("Подтверждение email — Стажировки KG", body, user.email)


def send_password_reset_email(user) -> bool:
    link = _link("/reset-password", user, password_reset_token.make_token(user))
    body = (
        "Здравствуйте!\n\n"
        "Чтобы задать новый пароль на платформе «Стажировки KG», перейдите по ссылке:\n"
        f"{link}\n\n"
        "Ссылка одноразовая. Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо."
    )
    return _send("Восстановление пароля — Стажировки KG", body, user.email)
