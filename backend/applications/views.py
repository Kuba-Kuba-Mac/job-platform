from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsSeeker

from .models import Application
from .serializers import ApplicationCreateSerializer, SeekerApplicationSerializer
from .services import create_application


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
        return (
            Application.objects.filter(seeker=self.request.user)
            .select_related("vacancy__company", "resume")
            .prefetch_related("vacancy__skills")
        )

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
