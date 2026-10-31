from django.contrib import admin

from .models import Resume, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["title", "full_name", "seeker", "city", "salary", "updated_at"]
    list_filter = ["city"]
    search_fields = ["title", "full_name", "seeker__email"]
    filter_horizontal = ["skills"]
