"""F-04: одноразовые токены для подтверждения email и сброса пароля.

Токены не хранятся в БД: в них зашит хеш состояния пользователя и время выдачи.
Как только состояние меняется (email подтверждён, пароль сменён), старая ссылка перестаёт работать.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import User


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "accounts.tokens.EmailVerificationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        # Смена email или подтверждение делают прежний токен недействительным
        return f"{user.pk}{user.email}{user.email_verified}{timestamp}"


email_verification_token = EmailVerificationTokenGenerator()
password_reset_token = default_token_generator


def encode_uid(user) -> str:
    return urlsafe_base64_encode(force_bytes(user.pk))


def user_from_uid(uid: str) -> User | None:
    try:
        pk = int(force_str(urlsafe_base64_decode(uid)))
    except (TypeError, ValueError, OverflowError):
        return None
    return User.objects.filter(pk=pk).first()
