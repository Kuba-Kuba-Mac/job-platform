from django.contrib import admin

from .models import Project, SeekerProfile


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0


@admin.register(SeekerProfile)
class SeekerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "github_url", "portfolio_url", "updated_at"]
    search_fields = ["user__email", "user__full_name"]
    inlines = [ProjectInline]
