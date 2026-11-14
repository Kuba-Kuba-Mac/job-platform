from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role, User
from .tokens import email_verification_token, password_reset_token, user_from_uid

INVALID_LINK = "Ссылка недействительна или устарела. Запросите новое письмо."


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "email_verified", "created_at"]
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


class PasswordChangeSerializer(serializers.Serializer):
    """F-03: смена пароля в личном кабинете."""

    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Текущий пароль указан неверно.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError({"new_password": "Новый пароль должен отличаться от текущего."})
        validate_new_password(attrs["new_password"], user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


def validate_new_password(password, user):
    try:
        password_validation.validate_password(password, user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"new_password": list(exc.messages)}) from exc


class UidTokenSerializer(serializers.Serializer):
    """Общая часть ссылок из писем: ?uid=…&token=…"""

    uid = serializers.CharField()
    token = serializers.CharField()
    token_generator = None

    def validate(self, attrs):
        user = user_from_uid(attrs["uid"])
        if user is None or not user.is_active or not self.token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": INVALID_LINK})
        attrs["user"] = user
        return attrs


class VerifyEmailSerializer(UidTokenSerializer):
    """F-04: подтверждение email. Токен одноразовый — после подтверждения хеш меняется."""

    token_generator = email_verification_token

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(UidTokenSerializer):
    """F-04: новый пароль по ссылке из письма. После смены пароля ссылка перестаёт работать."""

    token_generator = password_reset_token
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        attrs = super().validate(attrs)
        validate_new_password(attrs["new_password"], attrs["user"])
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class DetailSerializer(serializers.Serializer):
    """Ответ вида {"detail": "…"} (для Swagger)."""

    detail = serializers.CharField()


class TokenPairSerializer(serializers.Serializer):
    """Ответ смены пароля — новая пара токенов (для Swagger)."""

    access = serializers.CharField()
    refresh = serializers.CharField()
