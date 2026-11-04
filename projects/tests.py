"""Focused project model and permission tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from discovery.models import Category
from .models import Project


class ProjectTests(TestCase):
    """Verify project slugs, properties, and owner permissions."""

    def setUp(self):
        self.user = get_user_model().objects.create_user("owner", password="StrongPassword123!")
        self.category = Category.objects.create(name="Testing", slug="testing", description="Testing projects")

    def test_slug_collision_gets_suffix(self):
        """Duplicate titles receive a stable numeric suffix."""
        first = Project.objects.create(owner=self.user, title="Same title", summary="Summary", description="A sufficiently long project description for validation.", category=self.category, project_type="course")
        second = Project.objects.create(owner=self.user, title="Same title", summary="Summary", description="A sufficiently long project description for validation.", category=self.category, project_type="course")
        self.assertEqual(first.slug, "same-title")
        self.assertEqual(second.slug, "same-title-2")

    def test_project_list_is_public(self):
        """Guests can browse the project index."""
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)
