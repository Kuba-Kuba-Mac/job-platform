"""Единственное место, где создаются отклики и меняется их статус.

Письма N-01 (работодателю о новом отклике) и N-02 (соискателю о смене статуса) — точка 80%:
они подключатся receiver-ами к сигналам ниже, не трогая API и интерфейс.
Сигналы отправляются после коммита транзакции, чтобы письмо не ушло об отменённом изменении.
"""

from django.db import transaction
from django.dispatch import Signal

from .models import Application

# kwargs: application
application_created = Signal()


@transaction.atomic
def create_application(*, seeker, vacancy, resume, cover_letter=""):
    application = Application.objects.create(
        seeker=seeker, vacancy=vacancy, resume=resume, cover_letter=cover_letter.strip()
    )
    transaction.on_commit(lambda: application_created.send(sender=Application, application=application))
    return application
