import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="название")),
                ("description", models.TextField(blank=True, verbose_name="описание")),
                (
                    "logo",
                    models.ImageField(blank=True, null=True, upload_to="company_logos/", verbose_name="логотип"),
                ),
                ("city", models.CharField(blank=True, max_length=100, verbose_name="город")),
                ("phone", models.CharField(blank=True, max_length=32, verbose_name="телефон")),
                ("contact_email", models.EmailField(blank=True, max_length=254, verbose_name="контактный email")),
                ("website", models.URLField(blank=True, verbose_name="сайт")),
                (
                    "moderation_status",
                    models.CharField(
                        choices=[("pending", "На модерации"), ("approved", "Одобрена"), ("rejected", "Отклонена")],
                        default="pending",
                        max_length=16,
                        verbose_name="статус модерации",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="company",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="владелец",
                    ),
                ),
            ],
            options={
                "verbose_name": "компания",
                "verbose_name_plural": "компании",
                "ordering": ["name"],
            },
        ),
    ]
