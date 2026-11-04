"""Focused activity and upload validation tests."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from .forms import ResourceUploadForm


class ActivityTests(TestCase):
    """Verify resource extension and empty-file validation."""

    def test_empty_resource_is_rejected(self):
        """Zero-byte files cannot be uploaded."""
        
        form = ResourceUploadForm({"title": "Notes"}, {"file": SimpleUploadedFile("notes.txt", b"")})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)
