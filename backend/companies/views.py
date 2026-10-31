from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsEmployer

from .models import Company, ModerationStatus
from .serializers import CompanySerializer


class CompanyListView(generics.ListAPIView):
    """GET /api/companies/ — публичный список одобренных компаний."""

    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Company.objects.filter(moderation_status=ModerationStatus.APPROVED)


class CompanyDetailView(generics.RetrieveAPIView):
    """GET /api/companies/<id>/ — публичная страница одобренной компании."""

    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Company.objects.filter(moderation_status=ModerationStatus.APPROVED)


class MyCompanyView(APIView):
    """E-01: профиль компании текущего работодателя.

    GET    /api/companies/me/  — получить свой профиль
    POST   /api/companies/me/  — создать (если ещё нет)
    PATCH  /api/companies/me/  — изменить; после изменения компания снова уходит на модерацию
    """

    permission_classes = [IsEmployer]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    serializer_class = CompanySerializer

    def get_company(self, request):
        return Company.objects.filter(owner=request.user).first()

    def get(self, request):
        company = self.get_company(request)
        if company is None:
            return Response({"detail": "Профиль компании ещё не создан."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CompanySerializer(company).data)

    def post(self, request):
        if self.get_company(request):
            return Response({"detail": "Профиль компании уже существует."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        company = self.get_company(request)
        if company is None:
            return Response({"detail": "Профиль компании ещё не создан."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(moderation_status=ModerationStatus.PENDING)
        return Response(serializer.data)
