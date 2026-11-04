"""Admin configuration for discovery data."""

from django.contrib import admin
from .models import Category, Skill, UserSkill


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Configure category management."""

    list_display = ("name", "sort_order", "icon")
    search_fields = ("name", "description")
    ordering = ("sort_order", "name")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Configure skill management."""

    list_display = ("name", "group", "slug")
    list_filter = ("group",)
    search_fields = ("name", "slug")


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    """Configure member skill assignments."""

    list_display = ("user", "skill", "proficiency", "added_at")
    list_filter = ("proficiency", "skill__group")
    search_fields = ("user__username", "skill__name")
    raw_id_fields = ("user",)
    readonly_fields = ("added_at",)
