from django.conf import settings
from django.db import models


class Skill(models.Model):
    """Справочник навыков. Позже используется и вакансиями (E-02), и матчингом (X-01)."""

    name = models.CharField("название", max_length=64, unique=True)

    class Meta:
        verbose_name = "навык"
        verbose_name_plural = "навыки"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @staticmethod
    def normalize(name: str) -> str:
        return " ".join(name.split()).lower()


class Resume(models.Model):
    """S-01: резюме соискателя. У одного соискателя может быть несколько резюме."""

    seeker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes", verbose_name="соискатель"
    )
    title = models.CharField("желаемая должность", max_length=200)
    full_name = models.CharField("ФИО", max_length=200)
    city = models.CharField("город", max_length=100, blank=True)
    phone = models.CharField("телефон", max_length=32, blank=True)
    contact_email = models.EmailField("контактный email", blank=True)
    salary = models.PositiveIntegerField("желаемая зарплата, сом", null=True, blank=True)
    experience = models.TextField("опыт работы", blank=True)
    education = models.TextField("образование", blank=True)
    about = models.TextField("о себе", blank=True)
    languages = models.JSONField("языки", default=list, blank=True)
    skills = models.ManyToManyField(Skill, related_name="resumes", blank=True, verbose_name="навыки")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "резюме"
        verbose_name_plural = "резюме"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} — {self.full_name}"
