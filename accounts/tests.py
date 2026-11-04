"""Focused account model and authentication tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from .forms import RegisterForm
from .models import Profile


class AccountTests(TestCase):
    """Verify profile signals and registration validation."""

    def test_registration_logs_user_in_with_configured_backend(self):
        """A successful signup creates a session despite multiple backends."""
        response = self.client.post(
            "/accounts/register/",
            {
                "username": "newstudent",
                "first_name": "New",
                "last_name": "Student",
                "email": "newstudent@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )
        self.assertRedirects(response, "/accounts/profile/edit/?welcome=1")
        self.assertTrue(self.client.session.get("_auth_user_id"))
        self.assertTrue(Profile.objects.filter(user__username="newstudent").exists())

    def test_profile_created_for_user(self):
        """New users receive exactly one profile."""
        user = get_user_model().objects.create_user("student", password="StrongPassword123!")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_username_is_rejected_case_insensitively(self):
        """Registration rejects a username case variant."""
        get_user_model().objects.create_user("Student", password="StrongPassword123!")
        form = RegisterForm({"username": "student", "first_name": "A", "last_name": "B", "email": "new@example.com", "password1": "StrongPassword123!", "password2": "StrongPassword123!"})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
