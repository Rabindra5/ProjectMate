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



class Notification(models.Model):
    """Store in-app notifications for ProjectMate users."""

    TYPES = [
        ("request_received", "Join request received"),
        ("request_accepted", "Join request accepted"),
        ("request_rejected", "Join request rejected"),
        ("member_removed", "Removed from project"),
        ("project_update", "Project update"),
        ("general", "General notification"),
    ]

    # The user who will receive the notification.
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="notifications",
        on_delete=models.CASCADE,
    )

    notification_type = models.CharField(
        max_length=30,
        choices=TYPES,
        default="general",
    )

    # short title of the notification, e.g. "Join request received"
    title = models.CharField(max_length=150)

    # detailed message of the notification, e.g. "User X has requested to join your project."
    message = models.TextField(max_length=500)

    link = models.CharField(
        max_length=500,
        blank=True,
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"]
            ),
        ]

    def __str__(self):
        return f"{self.recipient}: {self.title}"
