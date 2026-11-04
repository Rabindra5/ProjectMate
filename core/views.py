"""Shared shell views and public pages."""

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import mail_admins
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import FormView, TemplateView

from .forms import BootstrapFormMixin
from .models import ContactMessage
from .team_data import TEAM_MEMBERS


class SafePaginationMixin:
    """Return the last page when a requested page is out of range."""

    def paginate_queryset(self, queryset, page_size):
        """Delegate pagination while gracefully handling invalid page values."""
        from django.core.paginator import Paginator

        paginator = Paginator(queryset, page_size)
        try:
            page_number = self.request.GET.get("page", 1)
            page = paginator.page(page_number)
        except (TypeError, ValueError):
            page = paginator.page(1)
        except Exception:
            page = paginator.page(paginator.num_pages or 1)
        return paginator, page, page.has_other_pages()


class IndexView(TemplateView):
    """Show the landing page or open the signed-in user's profile."""

    template_name = "core/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:profile", username=request.user.get_username())
        return super().get(request, *args, **kwargs)


class AboutView(TemplateView):
    """Explain the ProjectMate mission and workflow."""

    template_name = "core/about.html"


class TeamView(TemplateView):
    """Show the five student module owners."""

    template_name = "core/team.html"

    def get_context_data(self, **kwargs):
        """Add the documented team roster."""
        context = super().get_context_data(**kwargs)
        context["team_members"] = TEAM_MEMBERS
        return context


class ContactForm(BootstrapFormMixin, forms.Form):
    """Collect and validate a public contact message."""

    honeypot = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"] = forms.CharField(max_length=120)
        self.fields["email"] = forms.EmailField()
        self.fields["subject"] = forms.ChoiceField(choices=ContactMessage.SUBJECTS)
        self.fields["message"] = forms.CharField(max_length=2000, widget=forms.Textarea)
        self.fields["website"] = forms.CharField(required=False, label="Leave blank")

    def clean_website(self):
        """Reject automated submissions that fill the honeypot."""
        value = self.cleaned_data["website"]
        if value:
            raise forms.ValidationError("Invalid submission.")
        return value


class ContactView(FormView):
    """Save contact messages and notify the local development inbox."""

    template_name = "core/contact.html"
    form_class = ContactForm

    def form_valid(self, form):
        """Persist a message and apply a simple session throttle."""
        if self.request.session.get("contact_sent_at"):
            messages.info(self.request, "Please wait before sending another message.")
            return HttpResponseRedirect(reverse("core:contact"))

        message = ContactMessage.objects.create(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            subject=form.cleaned_data["subject"],
            message=form.cleaned_data["message"],
            user=self.request.user if self.request.user.is_authenticated else None,
        )
        self.request.session["contact_sent_at"] = True
        mail_admins(
            f"ProjectMate contact: {message.subject}",
            message.message,
            fail_silently=True,
        )
        messages.success(self.request, "Thanks. Your message has been sent.")
        return super().form_valid(form)

    def get_success_url(self):
        """Return to the contact page after submission."""
        return reverse("core:contact")


class PrivacyView(TemplateView):
    """Show the privacy notice."""

    template_name = "core/legal.html"
    extra_context = {
        "heading": "Privacy policy",
        "body": (
            "ProjectMate stores account, project, and functional activity data "
            "needed to operate the service. We do not sell student data."
        ),
    }


class TermsView(TemplateView):
    """Show the terms notice."""

    template_name = "core/legal.html"
    extra_context = {
        "heading": "Terms of service",
        "body": (
            "Use ProjectMate respectfully for genuine academic collaboration. "
            "Keep credentials private and upload only material you have permission to share."
        ),
    }


class FaqView(TemplateView):
    """Answer common ProjectMate questions."""

    template_name = "core/faq.html"
    extra_context = {
        "faqs": [
            ("What is ProjectMate?", "A student-focused place to discover projects and teammates."),
            ("Who can join?", "University of Windsor students and collaborators invited by project owners."),
            ("Can guests browse?", "Yes. Guests can browse public projects, while requests require an account."),
            ("How do requests work?", "Send a short application; the owner accepts or rejects it from their inbox."),
            ("Can I create a project?", "Authenticated members can create and manage their own projects."),
            ("What happens when a team is full?", "The project automatically stops accepting new requests."),
            ("Are resources private?", "Owners can mark resources public or team-only."),
            ("How is history stored?", "Functional sessions and signed cookies help provide recent activity and history."),
        ],
    }


class StyleguideView(TemplateView):
    """Render the design-system component showcase during development."""

    template_name = "styleguide.html"

    def dispatch(self, request, *args, **kwargs):
        """Hide the styleguide outside debug mode."""
        if not settings.DEBUG:
            return HttpResponseNotFound("Not found")
        return super().dispatch(request, *args, **kwargs)


def set_theme(request):
    """Store a validated theme preference in a cookie."""
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    theme = request.POST.get("theme", "light")
    next_url = request.POST.get("next", "/")
    if not url_has_allowed_host_and_scheme(
        next_url, {request.get_host()}, require_https=request.is_secure()
    ):
        next_url = "/"

    response = HttpResponseRedirect(next_url)
    response.set_cookie(
        "pm_theme",
        theme if theme in {"light", "dark"} else "light",
        max_age=31536000,
        samesite="Lax",
    )
    if request.POST.get("cookie_ok") == "1":
        response.set_cookie("pm_cookie_ok", "1", max_age=31536000, samesite="Lax")
    return response


def error_403(request, exception):
    """Return a forbidden response."""
    return HttpResponse("Access denied", status=403)


def error_404(request, exception):
    """Return a not-found response."""
    return HttpResponseNotFound("Page not found")


def error_500(request):
    """Return a server-error response."""
    return HttpResponseServerError("Something went wrong")