"""Request activity tracking middleware."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from django.utils import timezone
from .models import SiteVisit

logger = logging.getLogger(__name__)


class ActivityTrackingMiddleware:
    """Record safe successful page visits and signed browser counters."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Track a request after the view responds."""
        
        response = self.get_response(request)
        try:
            if request.method not in {"GET", "HEAD"} or response.status_code >= 400 or any(request.path.startswith(prefix) for prefix in ("/static/", "/media/", "/admin/", "/favicon", "/theme/")):
                return response
            if not request.session.session_key:
                request.session.create()
            today = timezone.now().astimezone(ZoneInfo("America/Toronto")).date()
            first_visit = request.session.get("pm_visit_date") != today.isoformat()
            if first_visit:
                previous = request.get_signed_cookie("pm_last_visit", default=None)
                request.pm_prev_visit = previous
                request.session["pm_visit_date"] = today.isoformat()
                request.session["pm_page_views_today"] = 1
                visits = int(request.get_signed_cookie("pm_visit_count", default="0") or 0) + 1
                response.set_signed_cookie("pm_visit_count", str(visits), max_age=31536000, httponly=True, samesite="Lax")
                response.set_signed_cookie("pm_last_visit", timezone.now().isoformat(), max_age=31536000, httponly=True, samesite="Lax")
                SiteVisit.objects.create(date=today, session_key=request.session.session_key, user=request.user if request.user.is_authenticated else None, first_seen=timezone.now())
            else:
                request.session["pm_page_views_today"] = request.session.get("pm_page_views_today", 0) + 1
                SiteVisit.objects.filter(date=today, session_key=request.session.session_key).update(page_views=request.session["pm_page_views_today"])
        except Exception:
            logger.exception("Activity tracking failed")
        return response
