from django.conf import settings
from django.db import models
from django.utils import timezone

from resumes.models import Resume
from vacancies.models import Vacancy


class ApplicationStatus(models.TextChoices):
    # Соискатель видит «new» как «Отправлен» (S-05), работодатель — как «Новый» (E-04)
    NEW = "new", "Новый"
    VIEWED = "viewed", "Просмотрен"
    INVITED = "invited", "Приглашение"
    REJECTED = "rejected", "Отказ"


class Application(models.Model):
    """S-04: отклик соискателя на вакансию. На одну вакансию — один отклик."""

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="applications", verbose_name="вакансия")
    seeker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications", verbose_name="соискатель"
    )
    # Если соискатель удалит резюме, отклик остаётся в истории обеих сторон
    resume = models.ForeignKey(
        Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name="applications", verbose_name="резюме"
    )
    cover_letter = models.TextField("сопроводительное письмо", blank=True)
    status = models.CharField("статус", max_length=16, choices=ApplicationStatus.choices, default=ApplicationStatus.NEW)
    status_changed_at = models.DateTimeField("статус изменён", default=timezone.now)
    created_at = models.DateTimeField("отправлен", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        verbose_name = "отклик"
        verbose_name_plural = "отклики"
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["vacancy", "seeker"], name="application_unique_vacancy_seeker")]
        indexes = [models.Index(fields=["vacancy", "status"], name="application_vacancy_status_idx")]

    def __str__(self):
        return f"{self.seeker} → {self.vacancy} ({self.get_status_display()})"
