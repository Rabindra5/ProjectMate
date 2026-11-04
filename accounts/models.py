"""Profile models for ProjectMate members."""

import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse


def profile_photo_path(instance, filename):
    """Store profile photos under a user-specific random name."""
    return f"profiles/{instance.user_id}/{uuid.uuid4()}{filename[filename.rfind('.'):]}"


class Profile(models.Model):
    """Store public student profile information separately from auth data."""

    YEARS = [("", "Choose year"), (1, "1st year"), (2, "2nd year"), (3, "3rd year"), (4, "4th year"), (5, "Master's"), (6, "PhD"), (7, "Other")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    photo = models.ImageField(upload_to=profile_photo_path, blank=True)
    headline = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    university = models.CharField(max_length=120, default="University of Windsor")
    program = models.CharField(max_length=100, blank=True)
    year_of_study = models.PositiveSmallIntegerField(choices=YEARS, blank=True, null=True)
    availability_hours = models.PositiveSmallIntegerField(default=5)
    open_to_teams = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_name(self):
        """Return a human-friendly name with username fallback."""
        return self.user.get_full_name().strip() or self.user.username

    @property
    def initials(self):
        """Return initials for avatar fallbacks."""
        return "".join(part[0] for part in self.display_name.split()[:2]).upper()

    def get_absolute_url(self):
        """Return the public profile URL."""
        return reverse("accounts:profile", kwargs={"username": self.user.username})

    def __str__(self):
        """Return the display name."""
        return self.display_name


class ProfileLink(models.Model):
    """Store one external link belonging to a profile."""

    LABELS = [("github", "GitHub"), ("linkedin", "LinkedIn"), ("portfolio", "Portfolio"), ("other", "Other")]
    profile = models.ForeignKey(Profile, related_name="links", on_delete=models.CASCADE)
    label = models.CharField(max_length=20, choices=LABELS)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "label"], condition=~models.Q(label="other"), name="unique_profile_link_label")]
        ordering = ["created_at"]

    def __str__(self):
        """Return the link label."""
        return f"{self.profile.display_name}: {self.get_label_display()}"
