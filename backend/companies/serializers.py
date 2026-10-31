from rest_framework import serializers

from .models import Company

MAX_LOGO_BYTES = 2 * 1024 * 1024


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "description",
            "logo",
            "city",
            "phone",
            "contact_email",
            "website",
            "moderation_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "moderation_status", "created_at", "updated_at"]

    def validate_logo(self, value):
        if value and value.size > MAX_LOGO_BYTES:
            raise serializers.ValidationError("Логотип должен быть не больше 2 МБ.")
        return value
