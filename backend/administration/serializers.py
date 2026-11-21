from rest_framework import serializers

from accounts.models import User


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
