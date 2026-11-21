from django.conf import settings
from django.db import models


class SeekerProfile(models.Model):
    """S-08: профиль студента — о себе, GitHub, портфолио и проекты."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seeker_profile", verbose_name="соискатель"
    )
    about = models.TextField("о себе", blank=True)
    github_url = models.URLField("GitHub", blank=True)
    portfolio_url = models.URLField("портфолио", blank=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        verbose_name = "профиль соискателя"
        verbose_name_plural = "профили соискателей"

    def __str__(self):
        return self.user.full_name or self.user.email


class Project(models.Model):
    """Проект студента: учебный, пет-проект или участие в open source."""

    MAX_PER_PROFILE = 20

    profile = models.ForeignKey(
        SeekerProfile, on_delete=models.CASCADE, related_name="projects", verbose_name="профиль"
    )
    title = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    url = models.URLField("ссылка", blank=True)
    technologies = models.CharField("технологии", max_length=255, blank=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "проект"
        verbose_name_plural = "проекты"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title
