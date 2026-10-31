from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "created_at"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """F-01: регистрация по email и паролю с выбором роли."""

    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    # Администратора через публичную регистрацию создать нельзя
    role = serializers.ChoiceField(choices=[Role.SEEKER, Role.EMPLOYER])

    class Meta:
        model = User
        fields = ["id", "email", "password", "role"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate(self, attrs):
        password_validation.validate_password(attrs["password"], User(email=attrs.get("email", "")))
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """F-02: вход; в ответ добавляем данные пользователя, в токен — роль."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
