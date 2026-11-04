"""Authentication and profile forms."""

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from core.forms import BootstrapFormMixin
from .models import Profile, ProfileLink
from .validators import validate_profile_image


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    """Register a student account with a unique username and email."""

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

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    """Edit public profile details and validate a new photo."""

    class Meta:
        model = Profile
        fields = ("photo", "headline", "bio", "university", "program", "year_of_study", "availability_hours", "open_to_teams")

    def clean_photo(self):
        """Apply the shared image validator."""
        photo = self.cleaned_data.get("photo")
        if photo:
            validate_profile_image(photo)
        return photo


class ProfileLinkForm(BootstrapFormMixin, forms.ModelForm):
    """Add a safe external profile link."""

    class Meta:
        model = ProfileLink
        fields = ("label", "url")
