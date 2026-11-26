"""Authentication and profile forms."""
import re

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from core.forms import BootstrapFormMixin
from .models import Profile, ProfileLink, ProfileDocument
from .validators import validate_profile_image, validate_resume, validate_document
from urllib.parse import urlsplit
from django.core.files.uploadedfile import UploadedFile


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    """Register a student account with a unique username and email."""
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def clean_username(self):
        """Reject usernames that differ only by case."""
        value = self.cleaned_data["username"].strip()
        if get_user_model().objects.filter(username__iexact=value).exists():
            raise forms.ValidationError("That username is already in use.")
        return value

    def clean_email(self):
        """Reject duplicate email addresses without case sensitivity."""
        value = self.cleaned_data["email"].strip()
        if get_user_model().objects.filter(email__iexact=value).exists():
            raise forms.ValidationError("That email is already in use.")
        return value


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """Authenticate with a username or email address."""

    username = forms.CharField(label="Username or email")
    remember_me = forms.BooleanField(required=False, initial=True)

    def clean(self):
        """Use the configured backend and keep errors generic."""
        identifier = self.cleaned_data.get("username", "").strip()
        password = self.cleaned_data.get("password")
        self.user_cache = authenticate(self.request, username=identifier, password=password)
        if self.user_cache is None:
            raise forms.ValidationError("Please enter a correct username/email and password.")
        return self.cleaned_data


class UserNameForm(BootstrapFormMixin, forms.ModelForm):
    """Edit the authenticated user's name and email."""

    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        """Ensure the email is not used by another account."""
        email = self.cleaned_data["email"].strip()

        existing_users = get_user_model().objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.pk)

        if existing_users.exists():
            raise forms.ValidationError(
                "That email is already in use."
            )

        return email


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    """Edit personal, academic and professional profile information."""
    program = forms.CharField(required=True, max_length=100)

    year_of_study = forms.TypedChoiceField(
        choices=Profile.YEARS,
        coerce=int,
        required=True,
    )

    class Meta:
        model = Profile
        fields = (
            "photo",
            "phone_number",
            "headline",
            "bio",
            "university",
            "program",
            "year_of_study",
            "availability_hours",
            "open_to_teams",
            "resume",
            "resume_is_public",
        )

        widgets = {
            "photo": forms.ClearableFileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.webp",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "type": "tel",
                    "placeholder": "+1 (519) 555-0123",
                    "autocomplete": "tel",
                }
            ),
            "resume": forms.FileInput(
                attrs={
                    "accept": ".pdf,.docx",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": 500,
                }
            ),
            "availability_hours": forms.NumberInput(
                attrs={
                    "min": 0,
                    "max": 168,
                }
            ),
        }

        help_texts = {
            "photo": "JPG, PNG or WEBP. Maximum 2 MB.",
            "phone_number": (
                "Optional. Your phone number is not displayed "
                "on your public profile."
            ),
            "resume": "PDF or DOCX. Maximum 5 MB.",
            "availability_hours": "Available hours per week.",
            "bio": "Tell other students about yourself.",
        }

    def clean_photo(self):
        """Validate newly uploaded profile photos."""
        photo = self.cleaned_data.get("photo")

        if isinstance(photo, UploadedFile):
            validate_profile_image(photo)

        return photo

    def clean_resume(self):
        """Validate newly uploaded resumes."""
        resume = self.cleaned_data.get("resume")

        if isinstance(resume, UploadedFile):
            validate_resume(resume)

        return resume

    def clean_availability_hours(self):
        """Validate weekly availability."""
        hours = self.cleaned_data["availability_hours"]

        if not 0 <= hours <= 168:
            raise forms.ValidationError(
                "Enter a value between 0 and 168 hours."
            )

        return hours

    def clean_phone_number(self):
        """Validate optional domestic and international phone numbers."""
        phone = self.cleaned_data.get("phone_number", "").strip()

        if not phone:
            return ""

        # Allow common phone number formatting characters.
        if not re.fullmatch(r"\+?[0-9\s().-]+", phone):
            raise forms.ValidationError(
                "Enter a valid phone number."
            )

        # Validate the number of digits without formatting characters.
        digits = re.sub(r"\D", "", phone)

        if not 7 <= len(digits) <= 15:
            raise forms.ValidationError(
                "Phone numbers must contain between 7 and 15 digits."
            )

        return phone


class ProfileLinkForm(BootstrapFormMixin, forms.ModelForm):
    """Add a safe external profile link."""

    class Meta:
        model = ProfileLink
        fields = ("label", "url")

class ProfileDocumentForm(BootstrapFormMixin, forms.ModelForm):
    """Upload a supporting document to a student profile."""

    class Meta:
        model = ProfileDocument
        fields = ("title", "file", "is_public")

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Java Certification",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "accept": ".pdf,.docx,.jpg,.jpeg,.png",
                }
            ),
        }

        help_texts = {
            "file": "PDF, DOCX, JPG or PNG. Maximum 5 MB.",
            "is_public": "Allow other users to download this document.",
        }

    def __init__(self, *args, profile=None, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)

    def clean_file(self):
        """Validate the uploaded supporting document."""
        document = self.cleaned_data["file"]
        validate_document(document)
        return document

    def clean(self):
        """Limit the number of supporting documents per profile."""
        cleaned_data = super().clean()

        if (
            self.profile
            and not self.instance.pk
            and self.profile.documents.count() >= 5
        ):
            raise forms.ValidationError(
                "You can upload a maximum of five supporting documents."
            )

        return cleaned_data
