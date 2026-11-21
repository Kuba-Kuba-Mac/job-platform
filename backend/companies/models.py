from django.conf import settings
from django.db import models


class ModerationStatus(models.TextChoices):
    PENDING = "pending", "На модерации"
    APPROVED = "approved", "Одобрена"
    REJECTED = "rejected", "Отклонена"


class Company(models.Model):
    """E-01: профиль компании. Один работодатель — одна компания."""

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company", verbose_name="владелец"
    )
    name = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    logo = models.ImageField("логотип", upload_to="company_logos/", blank=True, null=True)
    city = models.CharField("город", max_length=100, blank=True)
    phone = models.CharField("телефон", max_length=32, blank=True)
    contact_email = models.EmailField("контактный email", blank=True)
    website = models.URLField("сайт", blank=True)
    # A-02: новая или изменённая компания ждёт проверки администратора
    moderation_status = models.CharField(
        "статус модерации",
        max_length=16,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
        db_index=True,
    )
    rejection_reason = models.CharField("причина отклонения", max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "компания"
        verbose_name_plural = "компании"
        ordering = ["name"]

    def __str__(self):
        return self.name
