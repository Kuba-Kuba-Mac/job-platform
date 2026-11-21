from rest_framework import serializers

from companies.models import ModerationStatus
from vacancies.models import Vacancy
from vacancies.serializers import PublicVacancySerializer

from .models import Favorite


def is_published(vacancy):
    return (
        vacancy.moderation_status == ModerationStatus.APPROVED
        and not vacancy.is_archived
        and vacancy.company.moderation_status == ModerationStatus.APPROVED
    )


class FavoriteSerializer(serializers.ModelSerializer):
    """S-06. Добавление: {"vacancy_id": 5}. В списке — карточка вакансии и признак, доступна ли она сейчас."""

    vacancy = PublicVacancySerializer(read_only=True)
    vacancy_id = serializers.PrimaryKeyRelatedField(
        queryset=Vacancy.objects.select_related("company"), source="vacancy", write_only=True
    )
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ["id", "vacancy", "vacancy_id", "is_available", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_is_available(self, obj) -> bool:
        return is_published(obj.vacancy)

    def validate_vacancy_id(self, vacancy):
        if not is_published(vacancy):
            raise serializers.ValidationError("Эта вакансия недоступна.")
        if Favorite.objects.filter(user=self.context["request"].user, vacancy=vacancy).exists():
            raise serializers.ValidationError("Вакансия уже в избранном.")
        return vacancy
