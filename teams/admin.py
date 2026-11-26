"""Admin configuration for teams."""

from django.contrib import admin
from .models import JoinRequest, Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Configure membership administration."""

    list_display = ("project", "user", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("project__title", "user__username")
    raw_id_fields = ("project", "user")
    readonly_fields = ("joined_at",)


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    """Configure join request administration."""

    list_display = ("project", "applicant", "status", "created_at", "decided_at")
    list_filter = ("status", "created_at")
    search_fields = ("project__title", "applicant__username", "message")
    raw_id_fields = ("project", "applicant", "decided_by")
    readonly_fields = ("created_at",)
