"""Authentication and profile views."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    LogoutView as DjangoLogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from activity.models import ViewedProject

from .forms import (
    LoginForm,
    ProfileForm,
    ProfileLinkForm,
    RegisterForm,
    UserNameForm,
    ProfileDocumentForm,
)

from .models import Profile, ProfileLink, ProfileDocument
from pathlib import Path

from django.http import FileResponse, Http404
from django.views import View

from .validators import validate_profile_image


def get_user_profile(user):
    """Retrieve the user's profile or create it if missing."""
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def delete_file_after_commit(field):
    """Remove an unused file after a successful database transaction."""
    if field and field.name:
        storage = field.storage
        name = field.name

        transaction.on_commit(
            lambda: storage.delete(name),
            robust=True,
        )


def download_profile_file(field, filename):
    """Return a profile document as a downloadable attachment."""
    if not field:
        raise Http404("File not found.")

    try:
        file = field.open("rb")
    except FileNotFoundError as exc:
        raise Http404("File not found.") from exc

    response = FileResponse(
        file,
        as_attachment=True,
        filename=filename,
        content_type="application/octet-stream",
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"

    return response

class RegisterView(CreateView):
    """Create an account, log the student in, and create their profile."""

    form_class = RegisterForm
    template_name = "registration/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        super().form_valid(form)
        login(
            self.request,
            self.object,
            backend="accounts.backends.EmailOrUsernameBackend",
        )
        messages.success(
            self.request,
            "Welcome to ProjectMate. Complete your profile to get started.",
        )
        return redirect(f"{reverse_lazy('accounts:profile_edit')}?welcome=1")

    def get_success_url(self):
        return reverse_lazy("core:home")


class LoginView(DjangoLoginView):
    """Authenticate with a generic error and remember-me expiry."""

    authentication_form = LoginForm
    template_name = "registration/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session.set_expiry(
            1209600 if form.cleaned_data.get("remember_me") else 0
        )
        return response


class LogoutView(DjangoLogoutView):
    """Log out only in response to a POST request."""

    next_page = reverse_lazy("core:home")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been logged out.")
        return response

    def get(self, request, *args, **kwargs):
        return HttpResponse("Method not allowed", status=405)


class ProfileDetailView(DetailView):
    """Show a public profile with private history for its owner."""

    model = Profile
    template_name = "accounts/profile_detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Profile.objects.select_related("user"),
            user__username__iexact=self.kwargs["username"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viewer = self.request.user
        is_own_profile = viewer.is_authenticated and viewer.pk == self.object.user_id

        context["is_own_profile"] = is_own_profile
        context["profile_skills"] = self.object.user.user_skills.select_related("skill")

        if is_own_profile:
            context["recently_viewed"] = (
                ViewedProject.objects.filter(user=viewer)
                .select_related("project")
                .order_by("-last_viewed", "-pk")[:5]
            )
        # Only the owner can see private documents.
        documents = self.object.documents.all()

        if not is_own_profile:
            documents = documents.filter(is_public=True)

        context["documents"] = documents

        context["can_view_resume"] = bool(
            self.object.resume
            and (
                is_own_profile
                or self.object.resume_is_public
            )
        )

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update personal information, profile details and uploaded files."""

    template_name = "accounts/profile_form.html"
    form_class = ProfileForm

    def get_object(self, queryset=None):
        return get_user_profile(self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Preserve existing files before the form modifies the instance.
        old_photo = self.object.photo
        old_resume = self.object.resume

        profile_form = self.get_form()
        user_form = UserNameForm(
            request.POST,
            instance=request.user,
        )

        # Validate both forms so all errors can be displayed together.
        profile_valid = profile_form.is_valid()
        user_valid = user_form.is_valid()

        if profile_valid and user_valid:
            with transaction.atomic():
                profile = profile_form.save()
                user_form.save()

                # Remove replaced or cleared files after saving.
                if old_photo.name != profile.photo.name:
                    delete_file_after_commit(old_photo)

                if old_resume.name != profile.resume.name:
                    delete_file_after_commit(old_resume)

            messages.success(
                request,
                "Your profile has been updated.",
            )

            return redirect("accounts:profile_edit")

        return self.render_to_response(
            self.get_context_data(
                form=profile_form,
                user_form=user_form,
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.setdefault(
            "user_form",
            UserNameForm(instance=self.request.user),
        )

        context["documents"] = self.object.documents.all()
        context["profile_links"] = self.object.links.all()

        context["document_form"] = ProfileDocumentForm(
            profile=self.object,
        )

        return context

class ProfileLinkCreateView(LoginRequiredMixin, CreateView):
    """Add a link to the current profile."""

    model = ProfileLink
    form_class = ProfileLinkForm
    template_name = "accounts/profile_link_form.html"

    def form_valid(self, form):
        form.instance.profile = self.request.user.profile
        messages.success(self.request, "Profile link added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:profile_edit")

class ProfilePhotoUpdateView(LoginRequiredMixin, View):
    """Upload, replace or remove the current user's profile picture."""

    def post(self, request):
        profile = get_user_profile(request.user)
        old_photo = profile.photo

        # Remove the existing profile picture.
        if request.POST.get("remove") == "1":
            if profile.photo:
                with transaction.atomic():
                    profile.photo = ""
                    profile.save(
                        update_fields=["photo", "updated_at"]
                    )

                    delete_file_after_commit(old_photo)

                messages.success(
                    request,
                    "Profile picture removed.",
                )

            return redirect("accounts:profile_edit")

        # Retrieve the newly uploaded image.
        photo = request.FILES.get("photo")

        if not photo:
            messages.error(
                request,
                "Please select a profile picture."
            )
            return redirect("accounts:profile_edit")

        # Validate the image on the server before saving it.
        try:
            validate_profile_image(photo)

        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)

            return redirect("accounts:profile_edit")

        # Save the new picture and remove the previous file.
        with transaction.atomic():
            profile.photo = photo

            profile.save(
                update_fields=["photo", "updated_at"]
            )

            if old_photo.name != profile.photo.name:
                delete_file_after_commit(old_photo)

        messages.success(
            request,
            "Profile picture updated successfully.",
        )

        return redirect("accounts:profile_edit")

class ResumeDownloadView(View):
    """Allow downloads of public resumes or the owner's private resume."""

    def get(self, request, username):
        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user__username__iexact=username,
        )

        is_owner = (
            request.user.is_authenticated
            and request.user.pk == profile.user_id
        )

        if not is_owner and not profile.resume_is_public:
            raise Http404("Resume not found.")

        extension = Path(profile.resume.name or "").suffix

        return download_profile_file(
            profile.resume,
            f"resume{extension}",
        )


class ResumeDeleteView(LoginRequiredMixin, View):
    """Remove the authenticated user's resume."""

    def post(self, request):
        profile = get_user_profile(request.user)

        if profile.resume:
            old_resume = profile.resume

            with transaction.atomic():
                profile.resume = ""
                profile.resume_is_public = False

                profile.save(
                    update_fields=[
                        "resume",
                        "resume_is_public",
                        "updated_at",
                    ]
                )

                delete_file_after_commit(old_resume)

            messages.success(request, "Resume removed.")

        return redirect("accounts:profile_edit")


class ProfileDocumentCreateView(LoginRequiredMixin, View):
    """Upload a supporting document to the current user's profile."""

    def post(self, request):
        profile = get_user_profile(request.user)

        form = ProfileDocumentForm(
            request.POST,
            request.FILES,
            profile=profile,
        )

        if form.is_valid():
            document = form.save(commit=False)
            document.profile = profile
            document.original_filename = form.cleaned_data["file"].name
            document.save()

            messages.success(
                request,
                "Document uploaded successfully.",
            )
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)

        return redirect("accounts:profile_edit")


class ProfileDocumentDownloadView(View):
    """Download a document only when its visibility permits access."""

    def get(self, request, pk):
        document = get_object_or_404(
            ProfileDocument.objects.select_related("profile"),
            pk=pk,
        )

        is_owner = (
            request.user.is_authenticated
            and request.user.pk == document.profile.user_id
        )

        if not is_owner and not document.is_public:
            raise Http404("Document not found.")

        return download_profile_file(
            document.file,
            document.original_filename,
        )


class ProfileDocumentDeleteView(LoginRequiredMixin, View):
    """Delete a supporting document owned by the current user."""

    def post(self, request, pk):
        document = get_object_or_404(
            ProfileDocument,
            pk=pk,
            profile__user=request.user,
        )

        uploaded_file = document.file

        with transaction.atomic():
            document.delete()
            delete_file_after_commit(uploaded_file)

        messages.success(request, "Document removed.")

        return redirect("accounts:profile_edit")


class ProfileDocumentVisibilityView(LoginRequiredMixin, View):
    """Update the visibility of an owned supporting document."""

    def post(self, request, pk):
        document = get_object_or_404(
            ProfileDocument,
            pk=pk,
            profile__user=request.user,
        )

        document.is_public = (
            request.POST.get("is_public") == "1"
        )

        document.save(
            update_fields=["is_public", "updated_at"]
        )

        messages.success(
            request,
            "Document visibility updated.",
        )

        return redirect("accounts:profile_edit")


class ProfileLinkDeleteView(LoginRequiredMixin, DeleteView):
    """Delete only a link owned by the current user."""

    model = ProfileLink
    success_url = reverse_lazy("accounts:profile_edit")

    def get_queryset(self):
        return ProfileLink.objects.filter(profile__user=self.request.user)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Profile link removed.")
        return response

    def get(self, request, *args, **kwargs):
        return HttpResponse("Method not allowed", status=405)


PasswordChange = PasswordChangeView.as_view(
    template_name="registration/password_change_form.html",
    success_url=reverse_lazy("accounts:password_change_done"),
)
PasswordChangeDone = PasswordChangeDoneView.as_view(
    template_name="registration/password_change_done.html",
)
PasswordReset = PasswordResetView.as_view(
    template_name="registration/password_reset_form.html",
    email_template_name="registration/password_reset_email.txt",
    success_url=reverse_lazy("accounts:password_reset_done"),
)
PasswordResetDone = PasswordResetDoneView.as_view(
    template_name="registration/password_reset_done.html",
)
PasswordResetConfirm = PasswordResetConfirmView.as_view(
    template_name="registration/password_reset_confirm.html",
    success_url=reverse_lazy("accounts:password_reset_complete"),
)
PasswordResetComplete = PasswordResetCompleteView.as_view(
    template_name="registration/password_reset_complete.html",
)