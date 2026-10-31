"""F-06: ограничение доступа по ролям. Проверки выполняются на сервере."""

from rest_framework.permissions import BasePermission

from .models import Role


class HasRole(BasePermission):
    """Базовый класс: пропускает только аутентифицированных пользователей с нужной ролью."""

    allowed_roles: tuple[str, ...] = ()
    message = "Недостаточно прав для этой роли."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return user.role in self.allowed_roles


class IsSeeker(HasRole):
    allowed_roles = (Role.SEEKER,)
    message = "Доступно только соискателям."


class IsEmployer(HasRole):
    allowed_roles = (Role.EMPLOYER,)
    message = "Доступно только работодателям."


class IsPlatformAdmin(HasRole):
    allowed_roles = (Role.ADMIN,)
    message = "Доступно только администраторам."
