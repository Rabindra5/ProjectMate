
"""Shared template context."""

from datetime import datetime


def site(request):
    """Expose stable site values used by the shared layout."""

    theme = request.COOKIES.get("pm_theme", "light")

    pending_requests_count = 0
    unread_notifications_count = 0
    recent_notifications = []

    if request.user.is_authenticated:
        from teams.models import JoinRequest
        from .models import Notification

        # Count pending join requests for the user's projects
        pending_requests_count = JoinRequest.objects.filter(
            project__owner=request.user,
            status="pending",
        ).count()

        # this ensures that only logged-in user can view their notifications
        notifications = Notification.objects.filter(
            recipient=request.user,
        )

        # count unread notifications for the user
        unread_notifications_count = notifications.filter(
            is_read=False,
        ).count()

        recent_notifications = notifications.order_by(
            "-created_at"
        )[:5]

    return {
        "SITE_NAME": "ProjectMate",
        "current_year": datetime.now().year,
        "pm_theme": theme if theme in {"light", "dark"} else "light",
        "pm_cookie_ok": request.COOKIES.get("pm_cookie_ok") == "1",
        "pending_requests_count": pending_requests_count,
        "unread_notifications_count": unread_notifications_count,
        "recent_notifications": recent_notifications,
        "pm_prev_visit": getattr(request, "pm_prev_visit", None),
    }
