"""Project and project-update models."""

import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from discovery.models import Category, Skill
# from accounts.validators import validate_profile_image


def cover_path(instance, filename):
    """Store cover images under a random project-specific filename."""
    return f"projects/covers/{uuid.uuid4()}{filename[filename.rfind('.'):]}"


class Project(models.Model):
    """A student project seeking collaborators."""

    TYPES = [("course", "Course"), ("hackathon", "Hackathon"), ("competition", "Competition"), ("research", "Research"), ("personal", "Personal")]
    STATUSES = [("recruiting", "Recruiting"), ("full", "Full"), ("completed", "Completed")]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="owned_projects", on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    summary = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="projects")
    project_type = models.CharField(max_length=20, choices=TYPES)
    status = models.CharField(max_length=20, choices=STATUSES, default="recruiting")
    max_members = models.PositiveSmallIntegerField(default=2)
    required_skills = models.ManyToManyField(Skill, blank=True, related_name="projects")
    deadline = models.DateField(null=True, blank=True)
    is_remote = models.BooleanField(default=True)
    location = models.CharField(max_length=100, blank=True)
    repo_url = models.URLField(blank=True)
    cover_image = models.ImageField(upload_to=cover_path, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"]), models.Index(fields=["category"]), models.Index(fields=["project_type"])]

    def save(self, *args, **kwargs):
        """Create a stable unique slug on first save."""
        if not self.slug:
            base = slugify(self.title) or "project"
            candidate, number = base, 1
            while Project.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                number += 1
                candidate = f"{base}-{number}"
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        """Count memberships including the owner once teams is installed."""
        return self.memberships.count() if hasattr(self, "memberships") else 1

    @property
    def open_slots(self):
        """Return available places on the team."""
        return max(self.max_members - self.member_count, 0)

    @property
    def is_open(self):
        """Return whether new join requests are allowed."""
        return self.status == "recruiting" and self.open_slots > 0

    def get_absolute_url(self):
        """Return the project detail URL."""
        return reverse("projects:detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return the project title."""
        return self.title


class ProjectUpdate(models.Model):
    """A progress update posted by a project participant."""

    project = models.ForeignKey(Project, related_name="updates", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Return the update title."""
        return self.title
