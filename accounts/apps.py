"""Accounts application configuration."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configure account signals."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Register profile lifecycle signals."""
        from . import signals  # noqa: F401
