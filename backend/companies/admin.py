from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "city", "moderation_status", "created_at"]
    list_filter = ["moderation_status", "city"]
    search_fields = ["name", "owner__email"]
