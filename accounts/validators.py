"""Validation for profile images and supporting documents."""

from pathlib import Path
from zipfile import ZipFile, BadZipFile

from PIL import Image
from django.core.exceptions import ValidationError


def validate_profile_image(upload):
    """Validate the size, format and dimensions of a profile photo."""
    if upload.size > 2 * 1024 * 1024:
        raise ValidationError("Images must be 2 MB or smaller.")

    extension = Path(upload.name).suffix.lower()

    allowed_formats = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".webp": "WEBP",
    }

    if extension not in allowed_formats:
        raise ValidationError("Use a JPG, PNG, or WEBP image.")

    try:
        with Image.open(upload) as image:
            if image.format != allowed_formats[extension]:
                raise ValidationError(
                    "The image content does not match its file extension."
                )

            if image.width > 4096 or image.height > 4096:
                raise ValidationError(
                    "Image dimensions must not exceed 4096 x 4096 pixels."
                )

            image.verify()

    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("Upload a valid image file.") from exc
    finally:
        upload.seek(0)


def validate_document(upload, allowed_extensions=None):
    """Validate the size, extension and basic structure of a document."""
    if allowed_extensions is None:
        allowed_extensions = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}

    if upload.size == 0:
        raise ValidationError("The uploaded file is empty.")

    if upload.size > 5 * 1024 * 1024:
        raise ValidationError("Documents must be 5 MB or smaller.")

    extension = Path(upload.name).suffix.lower()

    if extension not in allowed_extensions:
        formats = ", ".join(
            sorted(ext.lstrip(".").upper() for ext in allowed_extensions)
        )
        raise ValidationError(f"Allowed file formats: {formats}.")

    try:
        if extension == ".pdf":
            if not upload.read(5).startswith(b"%PDF-"):
                raise ValidationError("Upload a valid PDF document.")

        elif extension == ".docx":
            with ZipFile(upload) as archive:
                required_files = {
                    "[Content_Types].xml",
                    "word/document.xml",
                }

                if not required_files.issubset(archive.namelist()):
                    raise ValidationError("Upload a valid DOCX document.")

        elif extension in {".jpg", ".jpeg", ".png"}:
            expected_format = "PNG" if extension == ".png" else "JPEG"

            with Image.open(upload) as image:
                if image.format != expected_format:
                    raise ValidationError("Invalid image format.")

                if image.width > 4096 or image.height > 4096:
                    raise ValidationError("Image dimensions are too large.")

                image.verify()

    except ValidationError:
        raise
    except (BadZipFile, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValidationError("Upload a valid document.") from exc
    finally:
        upload.seek(0)


def validate_resume(upload):
    """Restrict resume uploads to PDF and DOCX documents."""
    validate_document(
        upload,
        allowed_extensions={".pdf", ".docx"},
    )