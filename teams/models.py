"""Membership and join-request models."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from projects.models import Project


class Membership(models.Model):
    """Connect a user to a project team."""

    ROLES = [("owner", "Owner"), ("member", "Member")]
    project = models.ForeignKey(Project, related_name="memberships", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="memberships", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["project", "user"], name="unique_project_member")]
        ordering = ["joined_at"]

    def __str__(self):
        """Return a readable membership label."""
        return f"{self.user} in {self.project}"


class JoinRequest(models.Model):
    """Track a student's request to join a project."""

    STATUSES = [("pending", "Pending"), ("accepted", "Accepted"), ("rejected", "Rejected"), ("withdrawn", "Withdrawn"), ("cancelled", "Cancelled")]
    project = models.ForeignKey(Project, related_name="join_requests", on_delete=models.CASCADE)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="join_requests", on_delete=models.CASCADE)
    message = models.TextField(max_length=500)
    status = models.CharField(max_length=12, choices=STATUSES, default="pending")
    decision_note = models.CharField(max_length=300, blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="decided_requests", on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["project", "applicant"], condition=Q(status="pending"), name="unique_pending_join_request")]

    def __str__(self):
        """Return a readable request label."""
        return f"{self.applicant} → {self.project}"

    def get_absolute_url(self):
        """Return the request inbox URL."""
        return reverse("teams:request_inbox")
