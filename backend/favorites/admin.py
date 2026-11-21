from django.contrib import admin

from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "vacancy", "created_at"]
    search_fields = ["user__email", "vacancy__title"]
    list_select_related = ["user", "vacancy"]
