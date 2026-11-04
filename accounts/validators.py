"""Safe profile image validation."""

from io import BytesIO
from PIL import Image
from django.core.exceptions import ValidationError


def validate_profile_image(upload):
    """Validate extension, size, and image bytes for a profile photo."""
    if upload.size > 2 * 1024 * 1024:
        raise ValidationError("Images must be 2 MB or smaller.")
    extension = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
    if extension not in {"jpg", "jpeg", "png", "webp"}:
        raise ValidationError("Use a JPG, PNG, or WEBP image.")
    try:
        image = Image.open(BytesIO(upload.read()))
        image.verify()
    except Exception as exc:
        raise ValidationError("Upload a valid image file.") from exc
    finally:
        upload.seek(0)
