"""Activity recording helpers."""

from django.utils import timezone
from .models import ViewedProject


def record_project_view(request, project):
    """Record a member's project view without interrupting the response."""

    if request.user.is_authenticated:
        viewed, created = ViewedProject.objects.get_or_create(user=request.user, project=project, defaults={"last_viewed": timezone.now()})
        if not created:
            viewed.view_count += 1
            viewed.last_viewed = timezone.now()
            viewed.save(update_fields=["view_count", "last_viewed"])
    recent = request.session.get("recent_projects", [])
    request.session["recent_projects"] = [project.pk] + [pk for pk in recent if pk != project.pk][:9]


def record_search(request, params):
    """Keep a bounded list of recent search query strings."""

    searches = request.session.get("recent_searches", [])
    querystring = params.urlencode()
    if querystring:
        request.session["recent_searches"] = [querystring] + [item for item in searches if item != querystring][:7]


def merge_session_history_into_user(request, user):
    """Merge anonymous recent projects into member history on login."""
    
    from projects.models import Project
    for project_id in request.session.get("recent_projects", []):
        project = Project.objects.filter(pk=project_id).first()
        if project:
            ViewedProject.objects.get_or_create(user=user, project=project, defaults={"last_viewed": timezone.now()})
