"""Authentication and profile views."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from .forms import LoginForm, ProfileForm, ProfileLinkForm, RegisterForm, UserNameForm
from .models import Profile, ProfileLink


class RegisterView(CreateView):
    """Create an account, log the student in, and create their profile."""

    form_class = RegisterForm
    template_name = "registration/register.html"

    def dispatch(self, request, *args, **kwargs):
        """Send authenticated visitors back to the home page."""
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Log in the newly created user."""
        response = super().form_valid(form)
        login(self.request, self.object, backend="accounts.backends.EmailOrUsernameBackend")
        messages.success(self.request, "Welcome to ProjectMate. Complete your profile to get started.")
        return redirect(f"{reverse_lazy('accounts:profile_edit')}?welcome=1")

    def get_success_url(self):
        """Provide a fallback URL required by CreateView."""
        return reverse_lazy("core:home")


class LoginView(DjangoLoginView):
    """Authenticate with a generic error and remember-me expiry."""

    authentication_form = LoginForm
    template_name = "registration/login.html"

    def dispatch(self, request, *args, **kwargs):
        """Send authenticated visitors home."""
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Apply the selected session lifetime."""
        response = super().form_valid(form)
        self.request.session.set_expiry(1209600 if form.cleaned_data.get("remember_me") else 0)
        return response


class LogoutView(DjangoLogoutView):
    """Log out only in response to a POST request."""

    next_page = reverse_lazy("core:home")

    def post(self, request, *args, **kwargs):
        """Show a confirmation after logout."""
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been logged out.")
        return response

    def get(self, request, *args, **kwargs):
        """Reject unsafe logout GET requests."""
        return HttpResponse("Method not allowed", status=405)


class ProfileDetailView(DetailView):
    """Show a public profile without exposing the email address."""

    model = Profile
    template_name = "accounts/profile_detail.html"

    def get_object(self, queryset=None):
        """Resolve a profile by username."""
        return get_object_or_404(Profile.objects.select_related("user"), user__username__iexact=self.kwargs["username"])


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user and profile details together in one transaction."""

    template_name = "accounts/profile_form.html"
    form_class = ProfileForm

    def get_object(self, queryset=None):
        """Return the current user's profile."""
        return self.request.user.profile

    def post(self, request, *args, **kwargs):
        """Validate and save both related forms atomically."""
        self.object = self.get_object()
        profile_form = self.get_form()
        user_form = UserNameForm(request.POST, instance=request.user)
        if profile_form.is_valid() and user_form.is_valid():
            with transaction.atomic():
                profile_form.save()
                user_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile_edit")
        return self.render_to_response(self.get_context_data(form=profile_form, user_form=user_form))

    def get_context_data(self, **kwargs):
        """Expose the related name form."""
        context = super().get_context_data(**kwargs)
        context.setdefault("user_form", UserNameForm(instance=self.request.user))
        return context


class ProfileLinkCreateView(LoginRequiredMixin, CreateView):
    """Add a link to the current profile."""

    model = ProfileLink
    form_class = ProfileLinkForm
    template_name = "accounts/profile_link_form.html"

    def form_valid(self, form):
        """Associate the link with the current user."""
        form.instance.profile = self.request.user.profile
        messages.success(self.request, "Profile link added.")
        return super().form_valid(form)

    def get_success_url(self):
        """Return to profile editing."""
        return reverse_lazy("accounts:profile_edit")


class ProfileLinkDeleteView(LoginRequiredMixin, DeleteView):
    """Delete only a link owned by the current user."""

    model = ProfileLink
    success_url = reverse_lazy("accounts:profile_edit")

    def get_queryset(self):
        """Limit object access to the current profile."""
        return ProfileLink.objects.filter(profile__user=self.request.user)

    def post(self, request, *args, **kwargs):
        """Delete the link using POST and show feedback."""
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Profile link removed.")
        return response

    def get(self, request, *args, **kwargs):
        """Reject unsafe deletion GET requests."""
        return HttpResponse("Method not allowed", status=405)


PasswordChange = PasswordChangeView.as_view(template_name="registration/password_change_form.html", success_url=reverse_lazy("accounts:password_change_done"))
PasswordChangeDone = PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html")
PasswordReset = PasswordResetView.as_view(template_name="registration/password_reset_form.html", email_template_name="registration/password_reset_email.txt", success_url=reverse_lazy("accounts:password_reset_done"))
PasswordResetDone = PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html")
PasswordResetConfirm = PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html", success_url=reverse_lazy("accounts:password_reset_complete"))
PasswordResetComplete = PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html")
