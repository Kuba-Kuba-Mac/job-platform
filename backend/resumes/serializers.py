from rest_framework import serializers

from .models import Resume, Skill

MAX_SKILLS = 30
MAX_LANGUAGES = 10


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class ResumeSerializer(serializers.ModelSerializer):
    """S-01. Навыки передаются списком строк: ["python", "django"].
    Новые навыки создаются в справочнике автоматически."""

    skills = serializers.ListField(
        child=serializers.CharField(max_length=64), required=False, write_only=True, max_length=MAX_SKILLS
    )
    skill_list = serializers.SerializerMethodField()
    languages = serializers.ListField(
        child=serializers.CharField(max_length=64), required=False, max_length=MAX_LANGUAGES
    )

    class Meta:
        model = Resume
        fields = [
            "id",
            "title",
            "full_name",
            "city",
            "phone",
            "contact_email",
            "salary",
            "experience",
            "education",
            "about",
            "languages",
            "skills",
            "skill_list",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_skill_list(self, obj):
        return [s.name for s in obj.skills.all()]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # наружу отдаём навыки под понятным именем "skills"
        data["skills"] = data.pop("skill_list")
        return data

    def _set_skills(self, resume, names):
        normalized = {Skill.normalize(n) for n in names if n.strip()}
        skills = [Skill.objects.get_or_create(name=n)[0] for n in sorted(normalized)]
        resume.skills.set(skills)

    def create(self, validated_data):
        names = validated_data.pop("skills", [])
        resume = Resume.objects.create(**validated_data)
        self._set_skills(resume, names)
        return resume

    def update(self, instance, validated_data):
        names = validated_data.pop("skills", None)
        instance = super().update(instance, validated_data)
        if names is not None:
            self._set_skills(instance, names)
        return instance
