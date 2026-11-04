"""Team lifecycle signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.models import Project
from .models import Membership


@receiver(post_save, sender=Project)
def create_owner_membership(sender, instance, created, raw, **kwargs):
    """Create the owner membership when a project is first saved."""
    if raw or not created:
        return
    Membership.objects.get_or_create(project=instance, user=instance.owner, defaults={"role": "owner"})
