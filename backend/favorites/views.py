from django.db import IntegrityError, transaction
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from accounts.permissions import IsSeeker

from .models import Favorite
from .serializers import FavoriteSerializer


class FavoriteViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """S-06: избранные вакансии соискателя.

    GET    /api/favorites/       — своё избранное
    POST   /api/favorites/       — {"vacancy_id": 5}; повторно ту же вакансию добавить нельзя
    DELETE /api/favorites/{id}/  — убрать; чужие записи не видны (404)
    """

    serializer_class = FavoriteSerializer
    permission_classes = [IsSeeker]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("vacancy__company")
            .prefetch_related("vacancy__skills")
        )

    def perform_create(self, serializer):
        try:
            # двойной клик: проверка в сериализаторе могла пройти дважды, уникальный индекс — нет
            with transaction.atomic():
                serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({"vacancy_id": ["Вакансия уже в избранном."]}) from None
