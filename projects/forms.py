"""Project forms."""

from uuid import uuid4

from django import forms
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from accounts.validators import validate_profile_image
from core.forms import BootstrapFormMixin
from discovery.models import Skill

from .models import Project, ProjectUpdate


class ProjectForm(BootstrapFormMixin, forms.ModelForm):
    """Validate project details and save selected and custom skills."""

    custom_skill = forms.CharField(
        label="Add skill",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = Project
        fields = (
            "title",
            "summary",
            "description",
            "category",
            "project_type",
            "max_members",
            "required_skills",
            "deadline",
            "is_remote",
            "location",
            "repo_url",
            "cover_image",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "deadline": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "step": "60"},
            ),
            "required_skills": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        zone_name = timezone.get_current_timezone_name()
        self.fields["deadline"].help_text = (
            f"Choose a date and time. Time zone: {zone_name}."
        )

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Title cannot be blank.")
        return title

    def clean_custom_skill(self):
        names = []
        seen = set()

        for line in self.cleaned_data["custom_skill"].splitlines():
            name = " ".join(line.split())
            if not name:
                continue
            if len(name) > 80:
                raise forms.ValidationError(
                    "Each skill name must be 80 characters or fewer."
                )

            key = name.casefold()
            if key not in seen:
                names.append(name)
                seen.add(key)

        return names

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        if deadline and not self.instance.pk and deadline < timezone.now():
            raise forms.ValidationError("Choose a deadline in the future.")
        return deadline

    def clean_cover_image(self):
        image = self.cleaned_data.get("cover_image")
        if image:
            validate_profile_image(image)
        return image

    def clean_max_members(self):
        max_members = self.cleaned_data["max_members"]
        if self.instance.pk and max_members < self.instance.member_count:
            raise forms.ValidationError(
                f"This project already has {self.instance.member_count} members."
            )
        if max_members < 2 or max_members > 20:
            raise forms.ValidationError("Choose between 2 and 20 members.")
        return max_members

    @transaction.atomic
    def save(self, commit=True):
        return super().save(commit=commit)

    def _save_m2m(self):
        super()._save_m2m()

        for name in self.cleaned_data["custom_skill"]:
            slug_base = slugify(name)[:57].rstrip("-") or "skill"
            skill, _ = Skill.objects.get_or_create(
                name__iexact=name,
                defaults={
                    "name": name,
                    "slug": f"{slug_base}-{uuid4().hex}",
                    "group": "tools",
                },
            )
            self.instance.required_skills.add(skill)


class ProjectUpdateForm(BootstrapFormMixin, forms.ModelForm):
    """Create a project progress update."""

    class Meta:
        model = ProjectUpdate
        fields = ("title", "body")
        widgets = {"body": forms.Textarea}


class ProjectStatusForm(BootstrapFormMixin, forms.Form):
    """Choose a project status."""

    status = forms.ChoiceField(
        choices=(
            ("recruiting", "Recruiting"),
            ("completed", "Completed"),
        )
    )