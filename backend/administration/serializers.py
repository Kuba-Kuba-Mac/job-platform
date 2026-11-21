from rest_framework import serializers

from accounts.models import User
from companies.models import Company
from companies.serializers import CompanySerializer
from vacancies.models import Vacancy
from vacancies.serializers import FIELDS as VACANCY_FIELDS


class ModerationCompanyBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "city", "moderation_status"]


class ModerationVacancySerializer(serializers.ModelSerializer):
    """A-02: вакансия в очереди модерации — всё, что нужно, чтобы принять решение."""

    company = ModerationCompanyBriefSerializer(read_only=True)
    skills = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = Vacancy
        fields = [*VACANCY_FIELDS, "company", "moderation_status", "rejection_reason", "is_archived"]
        read_only_fields = fields


class ModerationCompanySerializer(CompanySerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta(CompanySerializer.Meta):
        fields = [*CompanySerializer.Meta.fields, "owner_email"]
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    """A-01: пользователь в списке администратора."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "full_name",
            "city",
            "email_verified",
            "is_active",
            "blocked_at",
            "block_reason",
            "last_login",
            "created_at",
        ]
        read_only_fields = fields


class BlockSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
