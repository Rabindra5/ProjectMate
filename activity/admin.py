"""Admin configuration for activity models."""

from django.contrib import admin
from .models import ProjectResource, SiteVisit, ViewedProject


@admin.register(ProjectResource)
class ProjectResourceAdmin(admin.ModelAdmin):
    """Configure resource administration."""

    list_display = ("title", "project", "uploaded_by", "is_public", "uploaded_at")
    list_filter = ("is_public", "uploaded_at")
    search_fields = ("title", "original_name", "project__title")
    raw_id_fields = ("project", "uploaded_by")
    readonly_fields = ("original_name", "size_bytes", "content_type", "uploaded_at")


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    """Configure visit aggregates."""

    list_display = ("date", "session_key", "user", "page_views")
    list_filter = ("date",)
    date_hierarchy = "date"


@admin.register(ViewedProject)
class ViewedProjectAdmin(admin.ModelAdmin):
    """Configure viewed-project history."""

    list_display = ("user", "project", "view_count", "last_viewed")
    raw_id_fields = ("user", "project")
    readonly_fields = ("last_viewed",)
