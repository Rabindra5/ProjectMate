
"""Project forms."""

from django import forms
from django.utils import timezone
from core.forms import BootstrapFormMixin
from accounts.validators import validate_profile_image
from .models import Project, ProjectUpdate


class ProjectForm(BootstrapFormMixin, forms.ModelForm):
    """Validate project details and optional cover images."""

    class Meta:
        model = Project
        fields = ("title", "summary", "description", "category", "project_type", "max_members", "required_skills", "deadline", "is_remote", "location", "repo_url", "cover_image")
        widgets = {"description": forms.Textarea}

    def clean_title(self):
        """Reject blank titles after trimming whitespace."""
        value = self.cleaned_data["title"].strip()
        if not value:
            raise forms.ValidationError("Title cannot be blank.")
        return value

    def clean_deadline(self):
        """Prevent new projects from starting with a past deadline."""
        value = self.cleaned_data.get("deadline")
        if value and not self.instance.pk and value < timezone.localdate():
            raise forms.ValidationError("Deadline cannot be in the past.")
        return value

    def clean_cover_image(self):
        """Apply the shared image validator."""
        image = self.cleaned_data.get("cover_image")
        if image:
            validate_profile_image(image)
        return image

    def clean_max_members(self):
        """Prevent reducing capacity below the current team size."""
        value = self.cleaned_data["max_members"]
        if self.instance.pk and value < self.instance.member_count:
            raise forms.ValidationError(f"This project already has {self.instance.member_count} members.")
        if value < 2 or value > 20:
            raise forms.ValidationError("Choose between 2 and 20 members.")
        return value
