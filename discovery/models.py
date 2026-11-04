"""Project categories and member skills."""

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse


class Category(models.Model):
    """Classify projects for browsing and filtering."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=50, default="bi-grid")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        """Return the category name."""
        return self.name


class Skill(models.Model):
    """Represent a skill that projects can request."""

    GROUPS = [("language", "Language"), ("framework", "Framework"), ("data", "Data & AI"), ("design", "Design"), ("tools", "Tools"), ("soft", "Soft skill")]
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    group = models.CharField(max_length=20, choices=GROUPS)

    class Meta:
        ordering = ["group", "name"]
        constraints = [models.UniqueConstraint(Lower("name"), name="skill_name_case_insensitive")]

    def __str__(self):
        """Return the skill name."""
        return self.name


class UserSkill(models.Model):
    """Connect a member to a skill and proficiency level."""

    PROFICIENCY = [(1, "Beginner"), (2, "Intermediate"), (3, "Advanced")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user_skills", on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, related_name="user_skills", on_delete=models.CASCADE)
    proficiency = models.PositiveSmallIntegerField(choices=PROFICIENCY, default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["skill__name"]
        constraints = [models.UniqueConstraint(fields=["user", "skill"], name="unique_user_skill")]

    def __str__(self):
        """Return a readable skill assignment."""
        return f"{self.user} - {self.skill}"

    def get_absolute_url(self):
        """Return the member's skill page."""
        return reverse("discovery:skills")
