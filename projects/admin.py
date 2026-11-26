"""Admin configuration for projects."""

from django.contrib import admin
from .models import Project, ProjectUpdate


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Configure project administration."""

    list_display = ("title", "owner", "category", "status", "project_type", "created_at")
    list_filter = ("status", "project_type", "category")
    search_fields = ("title", "summary", "description", "owner__username")
    raw_id_fields = ("owner",)
    filter_horizontal = ("required_skills",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    """Configure project update administration."""

    list_display = ("title", "project", "author", "created_at")
    search_fields = ("title", "body", "project__title")
    readonly_fields = ("created_at",)
