"""Resource and history forms."""

from django import forms
from core.forms import BootstrapFormMixin
from .models import ProjectResource


class ResourceUploadForm(BootstrapFormMixin, forms.ModelForm):
    """Validate a small, known resource file."""

    class Meta:
        model = ProjectResource
        fields = ("title", "description", "file", "is_public")

    def clean_file(self):
        """Reject empty or unsupported files."""
        upload = self.cleaned_data["file"]
        allowed = {"pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "md", "csv", "png", "jpg", "jpeg"}
        extension = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
        if upload.size == 0 or upload.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Files must be between 1 byte and 10 MB.")
        if extension not in allowed:
            raise forms.ValidationError("That file type is not supported.")
        return upload


class HistoryFilterForm(BootstrapFormMixin, forms.Form):
    """Choose the history range shown on the dashboard."""

    range = forms.ChoiceField(choices=(("7", "Last 7 days"), ("30", "Last 30 days"), ("all", "All time")), required=False)
