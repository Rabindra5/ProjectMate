"""Teams application configuration."""

from django.apps import AppConfig


class TeamsConfig(AppConfig):
    """Configure membership signals."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "teams"

    def ready(self):
        """Register project membership signals."""
        from . import signals  # noqa: F401
