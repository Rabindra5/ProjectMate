"""Shared template context."""

from datetime import datetime


def site(request):
    """Expose stable site values used by the shared layout."""
    theme = request.COOKIES.get("pm_theme", "light")
    pending_requests_count = 0
    if request.user.is_authenticated:
        from teams.models import JoinRequest
        pending_requests_count = JoinRequest.objects.filter(project__owner=request.user, status="pending").count()
    return {
        "SITE_NAME": "ProjectMate",
        "current_year": datetime.now().year,
        "pm_theme": theme if theme in {"light", "dark"} else "light",
        "pm_cookie_ok": request.COOKIES.get("pm_cookie_ok") == "1",
        "pending_requests_count": pending_requests_count,
        "pm_prev_visit": getattr(request, "pm_prev_visit", None),
    }
