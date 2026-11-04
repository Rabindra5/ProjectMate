"""Search and skill forms."""

from django import forms
from core.forms import BootstrapFormMixin
from .models import Category, Skill, UserSkill


class ProjectSearchForm(BootstrapFormMixin, forms.Form):
    """Validate optional project search filters."""

    q = forms.CharField(required=False, max_length=100)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label="All categories")
    project_type = forms.ChoiceField(choices=(("", "All types"), ("course", "Course"), ("hackathon", "Hackathon"), ("competition", "Competition"), ("research", "Research"), ("personal", "Personal")), required=False)
    status = forms.ChoiceField(choices=(("", "All statuses"), ("recruiting", "Recruiting"), ("full", "Full"), ("completed", "Completed")), required=False)
    skill = forms.ModelChoiceField(queryset=Skill.objects.all(), required=False, empty_label="All skills")
    sort = forms.ChoiceField(choices=(("newest", "Newest"), ("deadline", "Deadline"), ("open_slots", "Open slots"), ("best_match", "Best match")), required=False, initial="newest")

    def clean_q(self):
        """Trim user input before search."""
        return self.cleaned_data["q"].strip()


class PeopleSearchForm(BootstrapFormMixin, forms.Form):
    """Validate people finder filters."""

    q = forms.CharField(required=False, max_length=100)
    skill = forms.ModelChoiceField(queryset=Skill.objects.all(), required=False, empty_label="All skills")


class UserSkillForm(BootstrapFormMixin, forms.ModelForm):
    """Add a skill that the member does not already have."""

    class Meta:
        model = UserSkill
        fields = ("skill", "proficiency")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["skill"].queryset = Skill.objects.exclude(user_skills__user=user)

    def clean(self):
        """Limit profiles to 25 skills."""
        cleaned = super().clean()
        if self.user and self.user.user_skills.count() >= 25:
            raise forms.ValidationError("You can add up to 25 skills.")
        return cleaned
