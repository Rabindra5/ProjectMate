"""Focused team workflow tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from discovery.models import Category
from projects.models import Project
from .models import JoinRequest, Membership


class TeamTests(TestCase):
    """Verify owner membership and pending request constraints."""

    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user("owner", password="StrongPassword123!")
        self.applicant = User.objects.create_user("applicant", password="StrongPassword123!")
        category = Category.objects.create(name="Teams", slug="teams", description="Team projects")
        self.project = Project.objects.create(owner=self.owner, title="Team project", summary="Summary", description="A sufficiently long project description for validation.", category=category, project_type="course")

    def test_owner_membership_is_created(self):
        """The project owner is automatically a member."""
        self.assertTrue(Membership.objects.filter(project=self.project, user=self.owner, role="owner").exists())

    def test_pending_request_is_unique(self):
        """A second pending request violates the database constraint."""
        JoinRequest.objects.create(project=self.project, applicant=self.applicant, message="I can contribute useful project skills.")
        with self.assertRaises(Exception):
            JoinRequest.objects.create(project=self.project, applicant=self.applicant, message="I can contribute useful project skills.")
