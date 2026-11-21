from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["vacancy", "seeker", "status", "created_at", "status_changed_at"]
    list_filter = ["status"]
    search_fields = ["vacancy__title", "seeker__email"]
    list_select_related = ["vacancy", "seeker"]
    # статус меняет работодатель через сервис (E-04), чтобы не обойти будущие уведомления
    readonly_fields = ["status", "status_changed_at", "created_at", "updated_at"]
