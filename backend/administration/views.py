from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role, User
from accounts.permissions import IsPlatformAdmin
from accounts.services import block_user, unblock_user
from companies.models import Company, ModerationStatus
from vacancies.models import Vacancy

from .serializers import (
    AdminUserSerializer,
    BlockSerializer,
    ModerationCompanySerializer,
    ModerationVacancySerializer,
    RejectSerializer,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("q", str, description="Поиск по email и имени"),
            OpenApiParameter("role", str, enum=[r.value for r in Role]),
            OpenApiParameter("is_active", bool, description="false — только заблокированные"),
        ]
    )
)
class AdminUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """A-01: пользователи платформы для администратора.

    POST {id}/block/   — заблокировать (необязательная причина): вход запрещён, все токены перестают работать
    POST {id}/unblock/ — разблокировать
    """

    serializer_class = AdminUserSerializer
    permission_classes = [IsPlatformAdmin]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        qs = User.objects.order_by("-created_at")
        params = self.request.query_params
        if q := params.get("q", "").strip():
            qs = qs.filter(Q(email__icontains=q) | Q(full_name__icontains=q))
        if (role := params.get("role")) in Role.values:
            qs = qs.filter(role=role)
        if (active := params.get("is_active")) in ("true", "false"):
            qs = qs.filter(is_active=active == "true")
        return qs

    @extend_schema(request=BlockSerializer, responses={200: AdminUserSerializer})
    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response({"detail": "Нельзя заблокировать самого себя."}, status=status.HTTP_400_BAD_REQUEST)
        if user.is_platform_admin:
            return Response({"detail": "Нельзя заблокировать администратора."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = BlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        block_user(user, serializer.validated_data["reason"])
        return Response(self.get_serializer(user).data)

    @extend_schema(request=None, responses={200: AdminUserSerializer})
    @action(detail=True, methods=["post"])
    def unblock(self, request, pk=None):
        user = unblock_user(self.get_object())
        return Response(self.get_serializer(user).data)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "status",
                str,
                enum=[*ModerationStatus.values, "all"],
                description="По умолчанию pending — очередь на проверку",
            )
        ]
    )
)
class ModerationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """A-02: общая логика очереди модерации — одобрить или отклонить с причиной."""

    permission_classes = [IsPlatformAdmin]
    lookup_value_regex = r"\d+"
    base_queryset = None

    def get_queryset(self):
        qs = self.base_queryset.all()
        status_param = self.request.query_params.get("status", ModerationStatus.PENDING)
        if self.action == "list" and status_param != "all":
            qs = qs.filter(moderation_status=status_param)
        return qs

    def _decide(self, new_status, reason=""):
        obj = self.get_object()
        obj.moderation_status = new_status
        obj.rejection_reason = reason
        obj.save(update_fields=["moderation_status", "rejection_reason", "updated_at"])
        return Response(self.get_serializer(obj).data)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(ModerationStatus.APPROVED)

    @extend_schema(request=RejectSerializer)
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._decide(ModerationStatus.REJECTED, serializer.validated_data["reason"])


class VacancyModerationViewSet(ModerationViewSet):
    """GET /api/admin/moderation/vacancies/ — сначала самые старые, чтобы никто не ждал долго."""

    serializer_class = ModerationVacancySerializer
    base_queryset = (
        Vacancy.objects.select_related("company").prefetch_related("skills").order_by("created_at")
    )


class CompanyModerationViewSet(ModerationViewSet):
    serializer_class = ModerationCompanySerializer
    base_queryset = Company.objects.select_related("owner").order_by("created_at")
