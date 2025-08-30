from django.contrib import admin
from .models import Status

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("user", "text", "created_at")
    search_fields = ("text", "user__username")
