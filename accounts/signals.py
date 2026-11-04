"""Account lifecycle signals."""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, raw, **kwargs):
    """Create a profile for new users without duplicating fixture profiles."""
    if raw:
        return
    if created:
        Profile.objects.get_or_create(user=instance)
