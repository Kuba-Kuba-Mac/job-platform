from django.db.models import Count, OuterRef, Subquery
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role
from accounts.permissions import IsEmployer
from applications.models import Application
from companies.models import Company, ModerationStatus
from favorites.models import Favorite

from .filters import ORDERINGS, filter_vacancies
from .models import Vacancy
from .serializers import (
    CityCountSerializer,
    MyVacancySerializer,
    PublicVacancyDetailSerializer,
    PublicVacancySerializer,
)


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
        serializer.save(moderation_status=ModerationStatus.PENDING, rejection_reason="")

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


SEARCH_PARAMS = [
    OpenApiParameter("q", str, description="Текст: должность, описание, компания или навык"),
    OpenApiParameter("city", str, description="Город (без учёта регистра)"),
    OpenApiParameter("salary", int, description="Зарплата от, сом: вилка вакансии достигает этой суммы"),
    OpenApiParameter("experience", str, description="Через запятую: none, 1-3, 3-6, 6+"),
    OpenApiParameter("employment_type", str, description="Через запятую: full, part, project"),
    OpenApiParameter("schedule", str, description="Через запятую: full_day, shift, flexible, remote"),
    OpenApiParameter("internship", bool, description="true — только стажировки"),
    OpenApiParameter("ordering", str, enum=list(ORDERINGS), description="new (по умолчанию) или salary"),
    OpenApiParameter("page", int),
]


@extend_schema_view(list=extend_schema(parameters=SEARCH_PARAMS))
class VacancyViewSet(viewsets.ReadOnlyModelViewSet):
    """S-02/S-03: поиск и страница опубликованных вакансий — доступны и гостям."""

    serializer_class = PublicVacancySerializer
    permission_classes = [permissions.AllowAny]
    lookup_value_regex = r"\d+"

    def get_serializer_class(self):
        return PublicVacancyDetailSerializer if self.action == "retrieve" else PublicVacancySerializer

    def get_queryset(self):
        qs = Vacancy.objects.published().select_related("company").prefetch_related("skills")
        user = self.request.user
        if user.is_authenticated and user.role == Role.SEEKER:
            qs = qs.annotate(
                favorite_id=Subquery(Favorite.objects.filter(user=user, vacancy=OuterRef("pk")).values("id")[:1]),
                application_status=Subquery(
                    Application.objects.filter(seeker=user, vacancy=OuterRef("pk")).values("status")[:1]
                ),
            )
        if self.action == "list":
            qs = filter_vacancies(qs, self.request.query_params)
        return qs

    @extend_schema(responses={200: CityCountSerializer(many=True)})
    @action(detail=False, pagination_class=None)
    def cities(self, request):
        """Города с опубликованными вакансиями — для выпадающего списка фильтра."""
        rows = (
            Vacancy.objects.published().values("city").annotate(count=Count("id")).order_by("-count", "city")
        )
        return Response(list(rows))
