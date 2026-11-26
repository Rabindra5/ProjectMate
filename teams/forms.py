"""Team workflow forms."""

from django import forms
from core.forms import BootstrapFormMixin
from .models import JoinRequest


class JoinRequestForm(BootstrapFormMixin, forms.ModelForm):
    """Validate an applicant's join message."""

    class Meta:
        model = JoinRequest
        fields = ("message",)
        widgets = {"message": forms.Textarea}

    def clean_message(self):
        """Require a useful message rather than whitespace."""
        value = self.cleaned_data["message"].strip()
        if len(value) < 20:
            raise forms.ValidationError("Tell the owner a little more about your fit (at least 20 characters).")
        return value


class DecisionForm(BootstrapFormMixin, forms.Form):
    """Accept or reject a pending request."""

    action = forms.ChoiceField(choices=(("accept", "Accept"), ("reject", "Reject")))
    decision_note = forms.CharField(required=False, max_length=300, widget=forms.Textarea)


class RemoveMemberForm(BootstrapFormMixin, forms.Form):
    """Confirm removal of a project member."""

    confirm = forms.BooleanField(required=True)
