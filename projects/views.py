"""Project views."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import DatabaseError
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from activity.services import record_project_view
from teams.models import JoinRequest, Membership
from .forms import ProjectForm
from .models import Project

logger = logging.getLogger(__name__)



class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Create a project owned by the authenticated member."""

    model = Project
    form_class = ProjectForm
    template_name = "projects/form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Project created.")
        return super().form_valid(form)


class ProjectDetailView(DetailView):
    """Show project details and record successful page visits."""

    model = Project
    slug_url_kwarg = "slug"
    template_name = "projects/detail.html"

    def get_queryset(self):
        return (
            Project.objects.select_related("owner", "category")
            .prefetch_related("required_skills", "updates__author")
        )

    def get_context_data(self, **kwargs):
        """Provide membership and join request information."""
        context = super().get_context_data(**kwargs)

        user = self.request.user
        project = self.object

        context["is_member"] = False
        context["pending_request"] = None
        context["join_request_status"] = None

        if user.is_authenticated and project.owner_id != user.id:

            context["is_member"] = Membership.objects.filter(
                project=project,
                user=user,
            ).exists()

            latest_request = JoinRequest.objects.filter(
                project=project,
                applicant=user,
            ).order_by("-created_at", "-pk").first()

            if latest_request:
                context["join_request_status"] = latest_request.status

                if latest_request.status == "pending":
                    context["pending_request"] = latest_request

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        if request.method == "GET":
            response.add_post_render_callback(self.record_view)

        return response

    def record_view(self, response):
        """Keep the detail page available if saving history fails."""
        if response.status_code != 200:
            return

        try:
            record_project_view(self.request, self.object)
        except DatabaseError:
            logger.exception(
                "Could not record project view for project %s",
                self.object.pk,
            )


class ProjectOwnerMixin(UserPassesTestMixin):
    """Restrict project changes to owners and staff."""

    def test_func(self):
        user = self.request.user
        return self.get_object().owner_id == user.id or user.is_staff


class ProjectUpdateView(LoginRequiredMixin, ProjectOwnerMixin, UpdateView):
    """Edit an owned project."""

    model = Project
    form_class = ProjectForm
    template_name = "projects/form.html"
    slug_url_kwarg = "slug"

    def form_valid(self, form):
        messages.success(self.request, "Project updated.")
        return super().form_valid(form)


class ProjectDeleteView(LoginRequiredMixin, ProjectOwnerMixin, DeleteView):
    """Delete an owned project after confirmation."""

    model = Project
    template_name = "projects/confirm_delete.html"
    success_url = reverse_lazy("discovery:search")
    slug_url_kwarg = "slug"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Project deleted.")
        return response


class MyProjectsView(LoginRequiredMixin, ListView):
    """Show projects owned by the authenticated member."""

    model = Project
    template_name = "projects/mine.html"
    context_object_name = "projects"
    paginate_by = 9

    def get_queryset(self):
        """Return projects owned by the current user."""
        return (
            Project.objects.filter(owner=self.request.user)
            .select_related("owner", "category")
            .prefetch_related("required_skills")
        )
