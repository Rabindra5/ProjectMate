"""Shared form styling helpers."""

from django import forms


class BootstrapFormMixin:
    """Apply consistent Bootstrap classes to all ProjectMate forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                css_class = "form-select"
            elif isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            else:
                css_class = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css_class}".strip()
            if field.label and not isinstance(widget, (forms.CheckboxInput, forms.Select)):
                widget.attrs.setdefault("placeholder", field.label)
        for name, field in self.fields.items():
            if self.errors.get(name):
                field.widget.attrs["class"] += " is-invalid"
