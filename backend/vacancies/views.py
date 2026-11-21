from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsEmployer
from companies.models import Company, ModerationStatus

from .models import Vacancy
from .serializers import MyVacancySerializer, PublicVacancySerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[OpenApiParameter("archived", bool, description="true — архив, false — активные, без — все")]
    )
)
class MyVacancyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """E-02: «Мои вакансии» работодателя.

    Удаления нет — по ТЗ вакансия архивируется (POST {id}/archive/) и может быть восстановлена.
    Чужие вакансии в выборку не попадают (404). Любая правка снова отправляет вакансию на модерацию.
    """

    serializer_class = MyVacancySerializer
    permission_classes = [IsEmployer]
    http_method_names = ["get", "post", "patch", "head", "options"]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        qs = Vacancy.objects.filter(company__owner=self.request.user).prefetch_related("skills")
        archived = self.request.query_params.get("archived")
        if self.action == "list" and archived in ("true", "false"):
            qs = qs.filter(is_archived=archived == "true")
        return qs

    def create(self, request, *args, **kwargs):
        company = Company.objects.filter(owner=request.user).first()
        if company is None:
            return Response(
                {"detail": "Сначала создайте профиль компании — вакансии публикуются от её имени."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        serializer.save(moderation_status=ModerationStatus.PENDING)

    def _set_archived(self, value):
        vacancy = self.get_object()
        vacancy.is_archived = value
        vacancy.save(update_fields=["is_archived", "updated_at"])
        return Response(self.get_serializer(vacancy).data)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Перенести вакансию в архив — она перестаёт быть видна соискателям."""
        return self._set_archived(True)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """Вернуть вакансию из архива."""
        return self._set_archived(False)


class VacancyViewSet(viewsets.ReadOnlyModelViewSet):
    """Опубликованные вакансии для всех. Поиск с фильтрами (S-02) — на следующем этапе."""

    serializer_class = PublicVacancySerializer
    permission_classes = [permissions.AllowAny]
    lookup_value_regex = r"\d+"
    queryset = Vacancy.objects.published().select_related("company").prefetch_related("skills")
