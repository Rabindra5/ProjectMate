"""Storage for private profile documents."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateDocumentStorage(FileSystemStorage):
    """Store documents outside the public media directory."""

    @property
    def base_location(self):
        return str(settings.PRIVATE_MEDIA_ROOT)

    def url(self, name):
        """Require documents to use authorized download views."""
        raise NotImplementedError(
            "Documents must be accessed through authorized download views."
        )