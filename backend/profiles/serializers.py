from urllib.parse import urlparse

from rest_framework import serializers

from resumes.models import Skill

from .models import Project, SeekerProfile

GITHUB_HOSTS = {"github.com", "www.github.com"}


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "description", "url", "technologies", "created_at"]
        read_only_fields = ["id", "created_at"]


class SeekerProfileSerializer(serializers.ModelSerializer):
    """S-08. Имя и город берутся из профиля пользователя (F-05), навыки — из всех резюме (S-01).

    Email и телефон сюда не входят: профиль видят работодатели, а контакты — часть отклика (S-04).
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    city = serializers.CharField(source="user.city", read_only=True)
    skills = serializers.SerializerMethodField()
    projects = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = SeekerProfile
        fields = [
            "user_id",
            "full_name",
            "city",
            "about",
            "github_url",
            "portfolio_url",
            "skills",
            "projects",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def get_skills(self, obj) -> list[str]:
        skills = Skill.objects.filter(resumes__seeker_id=obj.user_id).distinct()
        return list(skills.values_list("name", flat=True))

    def validate_github_url(self, value):
        if value and urlparse(value).hostname not in GITHUB_HOSTS:
            raise serializers.ValidationError("Ссылка должна вести на github.com.")
        return value
