from django.conf import settings
from django.db import models

from vacancies.models import Vacancy


class Favorite(models.Model):
    """S-06: вакансия в избранном соискателя. Одну вакансию можно добавить только один раз."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites", verbose_name="соискатель"
    )
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="favorites", verbose_name="вакансия")
    created_at = models.DateTimeField("добавлена", auto_now_add=True)

    class Meta:
        verbose_name = "избранная вакансия"
        verbose_name_plural = "избранное"
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["user", "vacancy"], name="favorite_unique_user_vacancy")]

    def __str__(self):
        return f"{self.user} → {self.vacancy}"
