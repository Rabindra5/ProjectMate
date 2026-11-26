
"""Reusable services for ProjectMate."""
from .models import Notification


def create_notification(
    *,
    recipient,
    title,
    message,
    notification_type="general",
    link="",
):
    """Create an in-app notification for a user."""

    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )
