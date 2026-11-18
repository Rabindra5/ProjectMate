"""Project views."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import DatabaseError
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from activity.services import record_project_view

from .forms import ProjectForm
from .models import Project

logger = logging.getLogger(__name__)


class ProjectListView(ListView):
    """Display projects ordered by newest first."""

    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"
    paginate_by = 9

    def get_queryset(self):
        return (
            Project.objects.select_related("owner", "category")
            .prefetch_related("required_skills")
        )


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
    success_url = reverse_lazy("projects:list")
    slug_url_kwarg = "slug"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Project deleted.")
        return response