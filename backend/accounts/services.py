"""Операции над пользователями, которые нужны нескольким разделам (смена пароля, блокировка)."""

from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


def revoke_refresh_tokens(user):
    """Отзывает все refresh-токены пользователя — выход на всех устройствах."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


@transaction.atomic
def block_user(user, reason=""):
    """A-01: блокировка. Access-токены перестают работать сразу (simplejwt проверяет is_active),
    refresh-токены отзываются, войти заново нельзя."""
    user.is_active = False
    user.blocked_at = timezone.now()
    user.block_reason = reason.strip()
    user.save(update_fields=["is_active", "blocked_at", "block_reason"])
    revoke_refresh_tokens(user)
    return user


def unblock_user(user):
    user.is_active = True
    user.blocked_at = None
    user.block_reason = ""
    user.save(update_fields=["is_active", "blocked_at", "block_reason"])
    return user
