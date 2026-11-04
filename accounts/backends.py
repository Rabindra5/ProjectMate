"""Authentication backend supporting usernames and email addresses."""

from django.contrib.auth import get_user_model


class EmailOrUsernameBackend:
    """Authenticate a user by a case-insensitive username or unique email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Return a matching active user or ``None``."""
        identifier = (username or kwargs.get("email") or "").strip()
        if not identifier or password is None:
            return None
        users = get_user_model().objects.filter(username__iexact=identifier)
        if not users.exists():
            users = get_user_model().objects.filter(email__iexact=identifier)
        if users.count() != 1:
            return None
        user = users.first()
        return user if user and user.is_active and user.check_password(password) else None

    def get_user(self, user_id):
        """Load an active user for session authentication."""
        return get_user_model().objects.filter(pk=user_id, is_active=True).first()
