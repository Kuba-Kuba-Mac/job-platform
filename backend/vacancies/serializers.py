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


class PublicVacancySerializer(serializers.ModelSerializer):
    """Опубликованная вакансия для всех посетителей."""

    company = VacancyCompanySerializer(read_only=True)
    skills = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = Vacancy
        fields = [*FIELDS, "company"]
        read_only_fields = fields
