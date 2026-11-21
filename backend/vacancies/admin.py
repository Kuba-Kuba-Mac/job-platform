from django.contrib import admin

from .models import Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "city", "is_internship", "moderation_status", "is_archived", "created_at"]
    # Быстрая модерация прямо из списка, пока нет отдельного раздела A-02
    list_editable = ["moderation_status"]
    list_filter = ["moderation_status", "is_archived", "is_internship", "experience", "employment_type", "schedule"]
    search_fields = ["title", "company__name", "city"]
    filter_horizontal = ["skills"]
    list_select_related = ["company"]
