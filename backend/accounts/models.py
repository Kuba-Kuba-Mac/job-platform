from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.TextChoices):
    SEEKER = "seeker", "Соискатель"
    EMPLOYER = "employer", "Работодатель"
    ADMIN = "admin", "Администратор"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, role=Role.SEEKER, **extra):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, role=role, **extra)
        # F-03: set_password сохраняет только хеш (Argon2), сам пароль не хранится
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, role=Role.ADMIN, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь: вход по email, роль определяет доступные функции (F-01, F-06)."""

    email = models.EmailField("email", unique=True)
    role = models.CharField("роль", max_length=16, choices=Role.choices, default=Role.SEEKER)
    # F-04: вход без подтверждения не блокируется, но интерфейс просит подтвердить адрес
    email_verified = models.BooleanField("email подтверждён", default=False)
    # F-05: данные профиля, которые пользователь редактирует сам
    full_name = models.CharField("имя и фамилия", max_length=200, blank=True)
    phone = models.CharField("телефон", max_length=32, blank=True)
    city = models.CharField("город", max_length=100, blank=True)
    is_active = models.BooleanField("активен", default=True)
    is_staff = models.BooleanField("доступ в админку", default=False)
    created_at = models.DateTimeField("создан", auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_seeker(self):
        return self.role == Role.SEEKER

    @property
    def is_employer(self):
        return self.role == Role.EMPLOYER

    @property
    def is_platform_admin(self):
        return self.role == Role.ADMIN or self.is_superuser
