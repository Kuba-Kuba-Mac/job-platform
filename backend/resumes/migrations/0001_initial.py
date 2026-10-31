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
            name="Skill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, unique=True, verbose_name="название")),
            ],
            options={
                "verbose_name": "навык",
                "verbose_name_plural": "навыки",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Resume",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="желаемая должность")),
                ("full_name", models.CharField(max_length=200, verbose_name="ФИО")),
                ("city", models.CharField(blank=True, max_length=100, verbose_name="город")),
                ("phone", models.CharField(blank=True, max_length=32, verbose_name="телефон")),
                ("contact_email", models.EmailField(blank=True, max_length=254, verbose_name="контактный email")),
                (
                    "salary",
                    models.PositiveIntegerField(blank=True, null=True, verbose_name="желаемая зарплата, сом"),
                ),
                ("experience", models.TextField(blank=True, verbose_name="опыт работы")),
                ("education", models.TextField(blank=True, verbose_name="образование")),
                ("about", models.TextField(blank=True, verbose_name="о себе")),
                ("languages", models.JSONField(blank=True, default=list, verbose_name="языки")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "seeker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resumes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="соискатель",
                    ),
                ),
                (
                    "skills",
                    models.ManyToManyField(
                        blank=True, related_name="resumes", to="resumes.skill", verbose_name="навыки"
                    ),
                ),
            ],
            options={
                "verbose_name": "резюме",
                "verbose_name_plural": "резюме",
                "ordering": ["-updated_at"],
            },
        ),
    ]
