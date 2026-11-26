"""History and project resource models."""

import uuid
from django.conf import settings
from django.db import models
from projects.models import Project


def resource_path(instance, filename):
    """Store resources under a project with a random filename."""

    return f"resources/{instance.project_id}/{uuid.uuid4()}_{filename.rsplit('/', 1)[-1]}"


class ProjectResource(models.Model):
    """A document shared with a project's permitted audience."""

    project = models.ForeignKey(Project, related_name="resources", on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to=resource_path)
    original_name = models.CharField(max_length=255)
    size_bytes = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    is_public = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        """Return the resource title."""
        
        return self.title


class SiteVisit(models.Model):
    """Aggregate daily page views for a browser session."""

    date = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=40)
    page_views = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["date", "session_key"], name="unique_daily_session_visit")]


class ViewedProject(models.Model):
    """Track projects viewed by a logged-in member."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    view_count = models.PositiveIntegerField(default=1)
    last_viewed = models.DateTimeField()

    class Meta:
        ordering = ["-last_viewed"]
        constraints = [models.UniqueConstraint(fields=["user", "project"], name="unique_viewed_project")]
