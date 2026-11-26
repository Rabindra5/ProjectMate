"""Signals that merge anonymous history after authentication."""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .services import merge_session_history_into_user


@receiver(user_logged_in)
def merge_history(sender, request, user, **kwargs):
    """Merge recent anonymous project views after login."""
    
    merge_session_history_into_user(request, user)
