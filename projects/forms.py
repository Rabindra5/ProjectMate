"""Project forms."""

from uuid import uuid4

from django import forms
from django.utils import timezone
from django.utils.text import slugify

from discovery.models import Skill
from core.forms import BootstrapFormMixin
from accounts.validators import validate_profile_image
from .models import Project, ProjectUpdate


class ProjectForm(BootstrapFormMixin, forms.ModelForm):
    """Validate project details and optional cover images."""

    new_skills = forms.CharField(required=False, max_length=1000, widget=forms.HiddenInput)

    def clean_new_skills(self):
        names = [name.strip() for name in self.cleaned_data["new_skills"].splitlines()]
        if any(len(name) > 80 for name in names):
            raise forms.ValidationError("Skill names must be 80 characters or fewer.")
        return list(dict.fromkeys(name for name in names if name))

    def _save_m2m(self):
        super()._save_m2m()
        for name in self.cleaned_data["new_skills"]:
            slug = slugify(name)[:56] or "skill"
            skill, _ = Skill.objects.get_or_create(
                name__iexact=name,
                defaults={"name": name, "slug": f"{slug}-{uuid4().hex}", "group": "tools"},
            )
            self.instance.required_skills.add(skill)

    class Meta:
        model = Project
        fields = ("title", "summary", "description", "category", "project_type", "max_members", "required_skills", "deadline", "is_remote", "location", "repo_url", "cover_image")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "required_skills": forms.CheckboxSelectMultiple,
            "deadline": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }
        labels = {
            "max_members": "Maximum team size",
            "required_skills": "Skills needed",
            "cover_image": "Cover image (optional)",
            "is_remote": "Remote-friendly project",
            "repo_url": "Repository URL",
        }
        help_texts = {"summary": "One line shown on project cards."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["required_skills"].widget.attrs["class"] = "btn-check"

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
