"""Models shared by public ProjectMate pages."""

from django.conf import settings
from django.db import models


class ContactMessage(models.Model):
    """Store a visitor's message for the project team."""

    SUBJECTS = [
        ("general", "General"),
        ("bug", "Bug report"),
        ("partnership", "Partnership"),
        ("feedback", "Feedback"),
    ]
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=20, choices=SUBJECTS)
    message = models.TextField(max_length=2000)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Return a useful admin label."""
        return f"{self.subject}: {self.name}"
