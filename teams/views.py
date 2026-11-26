"""Join request and membership views."""
from core.services import create_notification
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, DetailView, FormView, ListView
from projects.models import Project
from projects.services import sync_project_status
from .forms import DecisionForm, JoinRequestForm, RemoveMemberForm
from .models import JoinRequest, MemberRemoval, Membership


def display_name(user):
    """Return a friendly name for messages and notifications."""
    return user.get_full_name() or user.username


class JoinRequestCreateView(LoginRequiredMixin, CreateView):
    """Apply to join an open project."""

    model = JoinRequest
    form_class = JoinRequestForm
    template_name = "teams/apply.html"

    def dispatch(self, request, *args, **kwargs):
        """Reject applications that violate basic project rules."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.project = get_object_or_404(Project, slug=kwargs["slug"])
        if self.project.owner_id == request.user.id or Membership.objects.filter(project=self.project, user=request.user).exists():
            messages.info(request, "You are already connected to this project.")
            return redirect(self.project)
        if not self.project.is_open or JoinRequest.objects.filter(project=self.project, applicant=request.user, status="pending").exists():
            messages.error(request, "This project is not accepting another request from you.")
            return redirect(self.project)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Set project and applicant server-side."""
        form.instance.project = self.project
        form.instance.applicant = self.request.user
        messages.success(self.request, "Your join request was sent.")
        return super().form_valid(form)

    def get_success_url(self):
        """Return to the project page."""
        return self.project.get_absolute_url()

    def get_context_data(self, **kwargs):
        """Show the project being applied to."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context


class MySentRequestsView(LoginRequiredMixin, ListView):
    """List requests sent by the current member."""

    model = JoinRequest
    template_name = "teams/my_requests.html"
    context_object_name = "requests"

    def get_queryset(self):
        """Load projects with each request."""
        return JoinRequest.objects.filter(applicant=self.request.user).select_related("project")

    def get_context_data(self, **kwargs):
        """Mark the active requests tab."""
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "sent"
        return context


class OwnerInboxView(LoginRequiredMixin, ListView):
    """List pending requests for projects owned by the member."""

    model = JoinRequest
    template_name = "teams/inbox.html"
    context_object_name = "requests"

    def get_queryset(self):
        """Scope the inbox to owned projects."""
        return JoinRequest.objects.filter(project__owner=self.request.user, status="pending").select_related("project", "applicant__profile")

    def get_context_data(self, **kwargs):
        """Add owned projects so owners can jump to team management."""
        context = super().get_context_data(**kwargs)
        context["owned_projects"] = Project.objects.filter(owner=self.request.user).prefetch_related("memberships")
        context["active_tab"] = "inbox"
        return context


class DecisionView(LoginRequiredMixin, FormView):
    """Accept or reject one pending request."""

    form_class = DecisionForm
    template_name = "teams/decision.html"

    def post(self, request, *args, **kwargs):
        """Apply a decision atomically after rechecking ownership and capacity."""
        join_request = get_object_or_404(
            JoinRequest.objects.select_related("project"),
            pk=kwargs["pk"],
            project__owner=request.user,
            status="pending",
        )

        form = self.form_class(request.POST)

        if not form.is_valid():
            messages.error(request, "Choose accept or reject.")
            return redirect("teams:request_inbox")

        with transaction.atomic():
            if (
                form.cleaned_data["action"] == "accept"
                and join_request.project.is_open
            ):
                Membership.objects.get_or_create(
                    project=join_request.project,
                    user=join_request.applicant,
                )
                join_request.status = "accepted"
                sync_project_status(join_request.project)

            elif form.cleaned_data["action"] == "accept":
                messages.error(request, "This project has no open slot.")
                return redirect("teams:request_inbox")

            else:
                join_request.status = "rejected"

            join_request.decision_note = form.cleaned_data["decision_note"]
            join_request.decided_by = request.user
            join_request.decided_at = timezone.now()

            join_request.save(
                update_fields=[
                    "status",
                    "decision_note",
                    "decided_by",
                    "decided_at",
                ]
            )

            # NEW: Notify the applicant when accepted.
            if join_request.status == "accepted":
                create_notification(
                    recipient=join_request.applicant,
                    notification_type="request_accepted",
                    title="Join request accepted",
                    message=(
                        f"Your request to join "
                        f"{join_request.project.title} "
                        "has been accepted."
                    ),
                    link=reverse("teams:my_requests"),
                )

            # NEW: Notify the applicant when rejected.
            elif join_request.status == "rejected":
                create_notification(
                    recipient=join_request.applicant,
                    notification_type="request_rejected",
                    title="Join request rejected",
                    message=(
                        f"Your request to join "
                        f"{join_request.project.title} "
                        "has been rejected."
                    ),
                    link=reverse("teams:my_requests"),
                )

        messages.success(
            request,
            f"{display_name(join_request.applicant)} was "
            f"{'added to the team' if join_request.status == 'accepted' else 'declined'}.",
        )
        return redirect("teams:request_inbox")

    def get(self, request, *args, **kwargs):
        """Reject GET for a decision action."""
        return HttpResponseNotAllowed(["POST"])


class WithdrawView(LoginRequiredMixin, FormView):
    """Withdraw a pending request owned by the applicant."""

    def post(self, request, *args, **kwargs):
        """Mark the request withdrawn."""
        join_request = get_object_or_404(JoinRequest, pk=kwargs["pk"], applicant=request.user, status="pending")
        join_request.status = "withdrawn"
        join_request.save(update_fields=["status"])
        messages.success(request, "Request withdrawn.")
        return redirect("teams:my_requests")

    def get(self, request, *args, **kwargs):
        """Reject GET for withdrawal."""
        return HttpResponseNotAllowed(["POST"])


class LeaveProjectView(LoginRequiredMixin, FormView):
    """Leave a project without allowing its owner to leave."""

    def post(self, request, *args, **kwargs):
        """Remove the current member and reopen capacity."""
        project = get_object_or_404(Project, slug=kwargs["slug"])
        membership = get_object_or_404(Membership, project=project, user=request.user)
        if membership.role == "owner":
            messages.error(request, "Transfer isn't supported; mark the project completed or delete it.")
        else:
            membership.delete()
            sync_project_status(project)

            # NEW: Tell the owner a spot opened up.
            create_notification(
                recipient=project.owner,
                title="A member left your project",
                message=f"{display_name(request.user)} left {project.title}. Their spot is open again.",
                link=reverse("teams:team", kwargs={"slug": project.slug}),
            )

            messages.success(request, "You left the project.")
        return redirect(project)

    def get(self, request, *args, **kwargs):
        """Reject GET for leaving a project."""
        return HttpResponseNotAllowed(["POST"])


class RemoveMemberView(LoginRequiredMixin, FormView):
    """Let the owner remove an accepted member with a recorded reason."""

    form_class = RemoveMemberForm

    def post(self, request, *args, **kwargs):
        """Record the reason, delete the membership and reopen the spot."""
        project = get_object_or_404(Project, slug=kwargs["slug"], owner=request.user)
        membership = get_object_or_404(Membership.objects.select_related("user"), project=project, user_id=kwargs["pk"], role="member")
        form = self.form_class(request.POST)
        if not form.is_valid():
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
            return redirect("teams:team", slug=project.slug)
        member = membership.user
        reason = form.cleaned_data["reason"]
        details = form.cleaned_data["details"]
        with transaction.atomic():
            MemberRemoval.objects.create(project=project, user=member, removed_by=request.user, reason=reason, details=details)
            membership.delete()
            JoinRequest.objects.filter(project=project, applicant=member, status="accepted").update(
                status="removed", decision_note=details, decided_by=request.user, decided_at=timezone.now()
            )
            sync_project_status(project)
            reason_label = dict(MemberRemoval.REASONS)[reason]
            create_notification(
                recipient=member,
                notification_type="member_removed",
                title=f"Removed from {project.title}"[:150],
                message=f"The owner removed you from {project.title}. Reason: {reason_label}. {details}"[:500],
                link=project.get_absolute_url(),
            )
        project.refresh_from_db()
        if project.is_open:
            messages.success(request, f"{display_name(member)} was removed. {project.open_slots} spot{'s' if project.open_slots != 1 else ''} now open for new members.")
        else:
            messages.success(request, f"{display_name(member)} was removed.")
        return redirect("teams:team", slug=project.slug)

    def get(self, request, *args, **kwargs):
        """Reject GET for member removal."""
        return HttpResponseNotAllowed(["POST"])


class TeamDetailView(LoginRequiredMixin, ListView):
    """Show team members to authenticated visitors."""

    model = Membership
    template_name = "teams/team.html"
    context_object_name = "members"

    def get_queryset(self):
        """Load the requested project's members."""
        self.project = get_object_or_404(Project, slug=self.kwargs["slug"])
        return Membership.objects.filter(project=self.project).select_related("user__profile")

    def get_context_data(self, **kwargs):
        """Add the project to the team template."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["is_owner"] = self.project.owner_id == self.request.user.id
        context["is_member"] = any(m.user_id == self.request.user.id for m in context["members"])
        if context["is_owner"]:
            context["remove_form"] = RemoveMemberForm()
            context["removals"] = self.project.member_removals.select_related("user")[:10]
            context["pending_count"] = self.project.join_requests.filter(status="pending").count()
        return context