from django.db import IntegrityError
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsEmployer, IsSeeker

from .models import Application, ApplicationStatus
from .serializers import (
    ApplicationCreateSerializer,
    EmployerApplicationDetailSerializer,
    SeekerApplicationSerializer,
    StatusChangeSerializer,
)
from .services import InvalidStatusTransition, change_status, create_application, mark_viewed


@extend_schema_view(list=extend_schema(parameters=[OpenApiParameter("status", str, enum=ApplicationStatus.values)]))
class SeekerApplicationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """S-04/S-05: отклики соискателя.

    POST /api/applications/      — откликнуться: своё резюме + сопроводительное письмо
    GET  /api/applications/      — «Мои отклики» со статусами
    GET  /api/applications/{id}/ — один свой отклик; чужие не видны (404)
    """

    permission_classes = [IsSeeker]
    lookup_value_regex = r"\d+"

    def get_serializer_class(self):
        return ApplicationCreateSerializer if self.action == "create" else SeekerApplicationSerializer

    def get_queryset(self):
        qs = (
            Application.objects.filter(seeker=self.request.user)
            .select_related("vacancy__company", "resume")
            .prefetch_related("vacancy__skills")
        )
        if self.action == "list" and (status_param := self.request.query_params.get("status")):
            if status_param not in ApplicationStatus.values:
                raise ValidationError({"status": f"Допустимо: {', '.join(ApplicationStatus.values)}."})
            qs = qs.filter(status=status_param)
        return qs

    @extend_schema(request=ApplicationCreateSerializer, responses={201: SeekerApplicationSerializer})
    def create(self, request, *args, **kwargs):
        serializer = ApplicationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            application = create_application(
                seeker=request.user,
                vacancy=data["vacancy_id"],
                resume=data["resume_id"],
                cover_letter=data["cover_letter"],
            )
        except IntegrityError:
            # одновременный двойной отклик: проверку прошли оба, уникальный индекс пропустил один
            raise ValidationError({"vacancy_id": ["Вы уже откликнулись на эту вакансию."]}) from None
        application = self.get_queryset().get(pk=application.pk)
        return Response(SeekerApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class EmployerApplicationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """E-03/E-04: отклик на вакансию работодателя с полным резюме кандидата.

    GET  /api/employer/applications/{id}/        — открыть; новый отклик становится «Просмотрен»
    POST /api/employer/applications/{id}/status/ — {"status": "viewed" | "invited" | "rejected"}
    Видны только отклики на свои вакансии; чужие — 404.
    Список откликов вакансии: GET /api/vacancies/my/{id}/applications/
    """

    serializer_class = EmployerApplicationDetailSerializer
    permission_classes = [IsEmployer]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return (
            Application.objects.filter(vacancy__company__owner=self.request.user)
            .select_related("seeker", "vacancy", "resume")
            .prefetch_related("resume__skills")
        )

    def retrieve(self, request, *args, **kwargs):
        application = mark_viewed(self.get_object(), by=request.user)
        return Response(self.get_serializer(application).data)

    @extend_schema(request=StatusChangeSerializer, responses={200: EmployerApplicationDetailSerializer})
    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        application = self.get_object()
        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            change_status(application, serializer.validated_data["status"], changed_by=request.user)
        except InvalidStatusTransition as exc:
            raise ValidationError({"status": [str(exc)]}) from None
        return Response(self.get_serializer(application).data)
