from rest_framework import serializers

from favorites.serializers import is_published
from resumes.models import Resume
from vacancies.models import Vacancy
from vacancies.serializers import PublicVacancySerializer

from .models import Application

MAX_COVER_LETTER = 3000


class ResumeBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ["id", "title"]


class ApplicationCreateSerializer(serializers.Serializer):
    """S-04: {"vacancy_id": 5, "resume_id": 2, "cover_letter": "…"}"""

    vacancy_id = serializers.PrimaryKeyRelatedField(queryset=Vacancy.objects.select_related("company"))
    resume_id = serializers.PrimaryKeyRelatedField(queryset=Resume.objects.all())
    cover_letter = serializers.CharField(max_length=MAX_COVER_LETTER, required=False, allow_blank=True, default="")

    def validate_vacancy_id(self, vacancy):
        if not is_published(vacancy):
            raise serializers.ValidationError("Откликнуться нельзя: вакансия снята с публикации или ещё не одобрена.")
        if Application.objects.filter(vacancy=vacancy, seeker=self.context["request"].user).exists():
            raise serializers.ValidationError("Вы уже откликнулись на эту вакансию.")
        return vacancy

    def validate_resume_id(self, resume):
        # чужое резюме — такой же ответ, как несуществующее
        if resume.seeker_id != self.context["request"].user.id:
            raise serializers.ValidationError("Резюме не найдено.")
        return resume


class SeekerApplicationSerializer(serializers.ModelSerializer):
    """S-05: отклик глазами соискателя."""

    vacancy = PublicVacancySerializer(read_only=True)
    resume = ResumeBriefSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ["id", "vacancy", "resume", "cover_letter", "status", "status_changed_at", "created_at"]
        read_only_fields = fields
