"""Единственное место, где создаются отклики и меняется их статус.

Письма N-01 (работодателю о новом отклике) и N-02 (соискателю о смене статуса) — точка 80%:
они подключатся receiver-ами к сигналам ниже, не трогая API и интерфейс.
Сигналы отправляются после коммита транзакции, чтобы письмо не ушло об отменённом изменении.
"""

from django.db import transaction
from django.dispatch import Signal
from django.utils import timezone

from .models import Application, ApplicationStatus

S = ApplicationStatus

# kwargs: application
application_created = Signal()
# kwargs: application, old_status, new_status, changed_by
application_status_changed = Signal()

# E-04: новый → просмотрен → приглашение / отказ; между приглашением и отказом можно передумать
ALLOWED_TRANSITIONS = {
    S.NEW: {S.VIEWED, S.INVITED, S.REJECTED},
    S.VIEWED: {S.INVITED, S.REJECTED},
    S.INVITED: {S.REJECTED},
    S.REJECTED: {S.INVITED},
}


class InvalidStatusTransition(Exception):
    pass


@transaction.atomic
def create_application(*, seeker, vacancy, resume, cover_letter=""):
    application = Application.objects.create(
        seeker=seeker, vacancy=vacancy, resume=resume, cover_letter=cover_letter.strip()
    )
    transaction.on_commit(lambda: application_created.send(sender=Application, application=application))
    return application


@transaction.atomic
def change_status(application, new_status, *, changed_by):
    """E-04: единственное место, где меняется статус отклика. Тот же статус — ничего не делаем."""
    old_status = application.status
    if new_status == old_status:
        return application
    if new_status not in ALLOWED_TRANSITIONS[old_status]:
        raise InvalidStatusTransition(f"Нельзя сменить статус «{S(old_status).label}» на «{S(new_status).label}».")
    application.status = new_status
    application.status_changed_at = timezone.now()
    application.save(update_fields=["status", "status_changed_at", "updated_at"])
    transaction.on_commit(
        lambda: application_status_changed.send(
            sender=Application,
            application=application,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
        )
    )
    return application


def mark_viewed(application, *, by):
    """Работодатель открыл новый отклик — он становится «Просмотрен»."""
    if application.status == S.NEW:
        change_status(application, S.VIEWED, changed_by=by)
    return application
