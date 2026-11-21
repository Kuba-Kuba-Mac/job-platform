from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role, User
from accounts.permissions import IsPlatformAdmin
from accounts.services import block_user, unblock_user

from .serializers import AdminUserSerializer, BlockSerializer


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
