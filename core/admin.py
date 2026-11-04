"""Admin configuration for core models."""

from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Configure contact message triage."""

    list_display = ("name", "email", "subject", "handled", "created_at")
    list_filter = ("subject", "handled", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("created_at",)
