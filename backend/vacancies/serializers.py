from rest_framework import serializers

from companies.models import Company
from resumes.models import Skill
from resumes.serializers import MAX_SKILLS

from .models import Vacancy

FIELDS = [
    "id",
    "title",
    "description",
    "city",
    "salary_from",
    "salary_to",
    "experience",
    "employment_type",
    "schedule",
    "is_internship",
    "skills",
    "created_at",
    "updated_at",
]


class VacancyCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "city", "logo"]


class MyVacancySerializer(serializers.ModelSerializer):
    """E-02: вакансия в кабинете работодателя. Навыки — список строк, как в резюме (S-01)."""

    skills = serializers.ListField(
        child=serializers.CharField(max_length=64), required=False, write_only=True, max_length=MAX_SKILLS
    )

    class Meta:
        model = Vacancy
        fields = [*FIELDS, "moderation_status", "rejection_reason", "is_archived"]
        read_only_fields = ["id", "moderation_status", "rejection_reason", "is_archived", "created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["skills"] = [s.name for s in instance.skills.all()]
        return data

    def validate(self, attrs):
        # При PATCH одно из значений может прийти, а второе остаться прежним
        salary_from = attrs.get("salary_from", getattr(self.instance, "salary_from", None))
        salary_to = attrs.get("salary_to", getattr(self.instance, "salary_to", None))
        if salary_from is not None and salary_to is not None and salary_from > salary_to:
            raise serializers.ValidationError({"salary_to": "Зарплата «до» не может быть меньше зарплаты «от»."})
        return attrs

    def create(self, validated_data):
        names = validated_data.pop("skills", [])
        vacancy = Vacancy.objects.create(**validated_data)
        vacancy.skills.set(Skill.from_names(names))
        return vacancy

    def update(self, instance, validated_data):
        names = validated_data.pop("skills", None)
        instance = super().update(instance, validated_data)
        if names is not None:
            instance.skills.set(Skill.from_names(names))
        return instance


class CityCountSerializer(serializers.Serializer):
    city = serializers.CharField()
    count = serializers.IntegerField()


class PublicVacancySerializer(serializers.ModelSerializer):
    """Опубликованная вакансия для всех посетителей.

    favorite_id — id записи в избранном текущего соискателя (S-06), иначе null;
    application_status — статус его отклика на эту вакансию (S-04/S-05), иначе null.
    Значения приходят аннотациями из запроса, поэтому лишних SQL-запросов нет.
    """

    company = VacancyCompanySerializer(read_only=True)
    skills = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    favorite_id = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = [*FIELDS, "company", "favorite_id", "application_status"]
        read_only_fields = fields

    def get_favorite_id(self, obj) -> int | None:
        return getattr(obj, "favorite_id", None)

    def get_application_status(self, obj) -> str | None:
        return getattr(obj, "application_status", None)


class VacancyCompanyDetailSerializer(serializers.ModelSerializer):
    """S-03: компания на странице вакансии — описание и публичные контакты."""

    class Meta:
        model = Company
        fields = ["id", "name", "city", "logo", "description", "website", "contact_email", "phone"]


class PublicVacancyDetailSerializer(PublicVacancySerializer):
    company = VacancyCompanyDetailSerializer(read_only=True)
