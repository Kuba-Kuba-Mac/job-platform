from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import send_password_reset_email, send_verification_email
from .models import User
from .serializers import (
    DetailSerializer,
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)

PASSWORD_RESET_SENT = "Если такой email зарегистрирован, мы отправили на него ссылку для восстановления пароля."


def revoke_refresh_tokens(user):
    """Отзывает все refresh-токены пользователя — выход на всех устройствах."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


class RegisterView(generics.CreateAPIView):
    """F-01: POST /api/auth/register/"""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # F-04: письмо с подтверждением; вход без подтверждения не блокируется
        send_verification_email(user)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """F-02: POST /api/auth/login/ → access + refresh + user"""

    serializer_class = LoginSerializer


class LogoutView(APIView):
    """F-02: POST /api/auth/logout/ — refresh-токен попадает в чёрный список."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Недействительный токен."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordChangeView(generics.GenericAPIView):
    """F-03: POST /api/auth/password/change/ — смена пароля.

    Все refresh-токены пользователя отзываются (выход на других устройствах),
    текущей сессии выдаётся новая пара токенов.
    """

    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: TokenPairSerializer})
    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        revoke_refresh_tokens(user)
        refresh = LoginSerializer.get_token(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


class VerifyEmailView(generics.GenericAPIView):
    """F-04: POST /api/auth/verify-email/ {uid, token} — подтверждение по ссылке из письма."""

    serializer_class = VerifyEmailSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    @extend_schema(responses={200: DetailSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Email подтверждён."})


class ResendVerificationView(generics.GenericAPIView):
    """F-04: POST /api/auth/verify-email/resend/ — отправить письмо подтверждения ещё раз."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DetailSerializer

    @extend_schema(request=None, responses={200: DetailSerializer, 400: DetailSerializer})
    def post(self, request):
        if request.user.email_verified:
            return Response({"detail": "Email уже подтверждён."}, status=status.HTTP_400_BAD_REQUEST)
        if not send_verification_email(request.user):
            return Response(
                {"detail": "Не удалось отправить письмо. Попробуйте позже."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"detail": f"Письмо отправлено на {request.user.email}."})


class PasswordResetView(generics.GenericAPIView):
    """F-04: POST /api/auth/password/reset/ {email} — «Забыли пароль?».

    Ответ одинаковый для существующего и несуществующего email,
    чтобы по нему нельзя было узнать, зарегистрирован ли адрес.
    Заблокированным пользователям письмо не отправляется.
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    @extend_schema(responses={200: DetailSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user is not None:
            send_password_reset_email(user)
        return Response({"detail": PASSWORD_RESET_SENT})


class PasswordResetConfirmView(generics.GenericAPIView):
    """F-04: POST /api/auth/password/reset/confirm/ {uid, token, new_password}.

    После смены пароля все refresh-токены отзываются, ссылка из письма становится недействительной.
    """

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    @extend_schema(responses={200: DetailSerializer})
    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        revoke_refresh_tokens(user)
        return Response({"detail": "Пароль изменён. Войдите с новым паролем."})


class MeView(generics.RetrieveUpdateAPIView):
    """F-05: «Мой профиль».

    GET   /api/auth/me/ — текущий пользователь и его роль
    PATCH /api/auth/me/ — изменить имя, телефон, город или email.
    При смене email адрес снова требует подтверждения (F-04).
    """

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user
