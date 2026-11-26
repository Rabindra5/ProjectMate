"""Admin configuration for student profiles and related records."""

from django.contrib import admin

from .models import Profile, ProfileLink, ProfileDocument


class ProfileLinkInline(admin.TabularInline):
    """Manage external links directly from a profile."""

    model = ProfileLink
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Manage student profiles and academic information."""

    list_display = (
        "display_name",
        "university",
        "program",
        "year_of_study",
        "availability_hours",
        "open_to_teams",
        "has_resume",
        "updated_at",
    )

    list_filter = (
        "university",
        "year_of_study",
        "open_to_teams",
        "resume_is_public",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "university",
        "program",
        "headline",
    )

    readonly_fields = ("created_at", "updated_at")

    # Keep private files behind the existing download permissions.
    exclude = ("resume",)

    list_select_related = ("user",)
    ordering = ("-updated_at",)
    list_per_page = 25

    inlines = [ProfileLinkInline]

    @admin.display(boolean=True, description="Resume uploaded")
    def has_resume(self, obj):
        """Indicate whether the student has uploaded a resume."""
        return bool(obj.resume)


@admin.register(ProfileLink)
class ProfileLinkAdmin(admin.ModelAdmin):
    """Manage external links associated with student profiles."""

    list_display = (
        "profile",
        "label",
        "url",
        "created_at",
    )

    list_filter = ("label", "created_at")

    search_fields = (
        "profile__user__username",
        "profile__user__first_name",
        "profile__user__last_name",
        "url",
    )

    readonly_fields = ("created_at",)
    list_select_related = ("profile__user",)
    ordering = ("-created_at",)
    list_per_page = 25


@admin.register(ProfileDocument)
class ProfileDocumentAdmin(admin.ModelAdmin):
    """Manage supporting document metadata and visibility."""

    list_display = (
        "title",
        "profile",
        "original_filename",
        "is_public",
    )

    list_filter = ("is_public",)

    search_fields = (
        "title",
        "original_filename",
        "profile__user__username",
        "profile__user__first_name",
        "profile__user__last_name",
    )

    readonly_fields = (
        "profile",
        "original_filename",
    )

    exclude = ("file",)

    list_select_related = ("profile__user",)
    list_per_page = 25

    def has_add_permission(self, request):
        """Require document uploads to use the validated profile flow."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Keep document deletion within the existing cleanup flow."""
        return False


from django.contrib import admin

# Register your models here.
