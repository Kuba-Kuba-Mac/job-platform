from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import Role, User
from accounts.permissions import IsSeeker

from .models import Project, SeekerProfile
from .serializers import ProjectSerializer, SeekerProfileSerializer


def profile_of(user):
    """Профиль создаётся при первом обращении — отдельный шаг «создать профиль» не нужен."""
    return SeekerProfile.objects.get_or_create(user=user)[0]


class MyProfileView(generics.RetrieveUpdateAPIView):
    """S-08: GET/PATCH /api/profiles/me/ — свой профиль студента."""

    serializer_class = SeekerProfileSerializer
    permission_classes = [IsSeeker]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return profile_of(self.request.user)


class MyProjectViewSet(viewsets.ModelViewSet):
    """S-08: /api/profiles/me/projects/ — свои проекты. Чужие не видны (404)."""

    serializer_class = ProjectSerializer
    permission_classes = [IsSeeker]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return Project.objects.filter(profile__user=self.request.user)

    def perform_create(self, serializer):
        profile = profile_of(self.request.user)
        if profile.projects.count() >= Project.MAX_PER_PROFILE:
            raise ValidationError({"detail": f"Можно добавить не больше {Project.MAX_PER_PROFILE} проектов."})
        serializer.save(profile=profile)


class SeekerProfileDetailView(generics.RetrieveAPIView):
    """S-08: GET /api/profiles/{user_id}/ — профиль студента глазами работодателя.

    Видят работодатель, администратор и сам соискатель; другой соискатель получает 403.
    """

    serializer_class = SeekerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        viewer = self.request.user
        if viewer.role == Role.SEEKER and viewer.pk != self.kwargs["user_id"] and not viewer.is_superuser:
            raise PermissionDenied("Профили других соискателей недоступны.")
        seeker = get_object_or_404(User, pk=self.kwargs["user_id"], role=Role.SEEKER, is_active=True)
        return profile_of(seeker)
