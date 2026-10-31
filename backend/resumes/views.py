from rest_framework import generics, permissions, viewsets

from accounts.permissions import IsSeeker

from .models import Resume, Skill
from .serializers import ResumeSerializer, SkillSerializer


class ResumeViewSet(viewsets.ModelViewSet):
    """S-01: соискатель создаёт, смотрит, редактирует и удаляет СВОИ резюме.

    Чужие резюме в этой выборке не видны (404), поэтому их нельзя ни прочитать, ни изменить.
    Просмотр резюме работодателем — функции E-03/E-05, они делаются позже.
    """

    serializer_class = ResumeSerializer
    permission_classes = [IsSeeker]

    def get_queryset(self):
        return Resume.objects.filter(seeker=self.request.user).prefetch_related("skills")

    def perform_create(self, serializer):
        serializer.save(seeker=self.request.user)


class SkillListView(generics.ListAPIView):
    """GET /api/skills/?q=py — подсказки навыков для формы резюме."""

    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Skill.objects.all()
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(name__icontains=q.strip().lower())
        return qs[:20]
