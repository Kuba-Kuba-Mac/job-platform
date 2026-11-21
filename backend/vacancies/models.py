from django.db import models

from companies.models import Company, ModerationStatus
from resumes.models import Skill


class Experience(models.TextChoices):
    NONE = "none", "Без опыта"
    FROM_1_TO_3 = "1-3", "1–3 года"
    FROM_3_TO_6 = "3-6", "3–6 лет"
    MORE_THAN_6 = "6+", "Более 6 лет"


class EmploymentType(models.TextChoices):
    FULL = "full", "Полная занятость"
    PART = "part", "Частичная занятость"
    PROJECT = "project", "Проектная работа"


class Schedule(models.TextChoices):
    FULL_DAY = "full_day", "Полный день"
    SHIFT = "shift", "Сменный график"
    FLEXIBLE = "flexible", "Гибкий график"
    REMOTE = "remote", "Удалённая работа"


class VacancyQuerySet(models.QuerySet):
    def published(self):
        """Видны всем: вакансия одобрена, не в архиве, и компания тоже одобрена."""
        return self.filter(
            moderation_status=ModerationStatus.APPROVED,
            is_archived=False,
            company__moderation_status=ModerationStatus.APPROVED,
        )


class Vacancy(models.Model):
    """E-02: вакансия компании. Удаления нет — по ТЗ вакансия уходит в архив."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="vacancies", verbose_name="компания")
    title = models.CharField("должность", max_length=200)
    description = models.TextField("описание")
    city = models.CharField("город", max_length=100)
    salary_from = models.PositiveIntegerField("зарплата от, сом", null=True, blank=True)
    salary_to = models.PositiveIntegerField("зарплата до, сом", null=True, blank=True)
    experience = models.CharField("опыт", max_length=8, choices=Experience.choices, default=Experience.NONE)
    employment_type = models.CharField(
        "тип занятости", max_length=16, choices=EmploymentType.choices, default=EmploymentType.FULL
    )
    schedule = models.CharField("график", max_length=16, choices=Schedule.choices, default=Schedule.FULL_DAY)
    is_internship = models.BooleanField("стажировка", default=False)
    skills = models.ManyToManyField(Skill, related_name="vacancies", blank=True, verbose_name="навыки")
    # Модерацию (A-02) делает администратор; любая правка снова отправляет вакансию на проверку
    moderation_status = models.CharField(
        "статус модерации", max_length=16, choices=ModerationStatus.choices, default=ModerationStatus.PENDING
    )
    rejection_reason = models.CharField("причина отклонения", max_length=500, blank=True)
    is_archived = models.BooleanField("в архиве", default=False)
    created_at = models.DateTimeField("создана", auto_now_add=True)
    updated_at = models.DateTimeField("изменена", auto_now=True)

    objects = VacancyQuerySet.as_manager()

    class Meta:
        verbose_name = "вакансия"
        verbose_name_plural = "вакансии"
        ordering = ["-created_at"]
        # S-02: поиск по опубликованным вакансиям — индексы на условия публикации и поля фильтров
        indexes = [
            models.Index(fields=["moderation_status", "is_archived", "-created_at"], name="vacancy_published_idx"),
            models.Index(fields=["city"], name="vacancy_city_idx"),
            models.Index(fields=["experience"], name="vacancy_experience_idx"),
            models.Index(fields=["employment_type"], name="vacancy_employment_idx"),
            models.Index(fields=["schedule"], name="vacancy_schedule_idx"),
            models.Index(fields=["is_internship"], name="vacancy_internship_idx"),
            models.Index(fields=["salary_from"], name="vacancy_salary_from_idx"),
            models.Index(fields=["salary_to"], name="vacancy_salary_to_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(salary_from__isnull=True)
                | models.Q(salary_to__isnull=True)
                | models.Q(salary_from__lte=models.F("salary_to")),
                name="vacancy_salary_range_valid",
            )
        ]

    def __str__(self):
        return f"{self.title} — {self.company}"
