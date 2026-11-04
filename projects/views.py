"""Project CRUD and detail views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from .forms import ProjectForm, ProjectStatusForm, ProjectUpdateForm
from .models import Project, ProjectUpdate


class ProjectListView(ListView):
    """Browse projects newest first."""

    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"
    paginate_by = 9

    def get_queryset(self):
        """Load category and owner in the list query."""
        return Project.objects.select_related("owner", "category").prefetch_related("required_skills")


class MyProjectsView(LoginRequiredMixin, ListView):
    """List projects owned by or joined by the current member."""

    model = Project
    template_name = "projects/mine.html"
    context_object_name = "projects"

    def get_queryset(self):
        """Return owned projects until membership filtering is available."""
        return Project.objects.filter(owner=self.request.user).select_related("category")


class ProjectDetailView(DetailView):
    """Show a project and its public collaboration details."""

    model = Project
    slug_url_kwarg = "slug"
    template_name = "projects/detail.html"

    def get_queryset(self):
        """Avoid N+1 queries for project cards."""
        return Project.objects.select_related("owner", "category").prefetch_related("required_skills", "updates__author")


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Create a project owned by the authenticated member."""

    model = Project
    form_class = ProjectForm
    template_name = "projects/form.html"

    def form_valid(self, form):
        """Set ownership from the session."""
        form.instance.owner = self.request.user
        messages.success(self.request, "Project created.")
        return super().form_valid(form)


class ProjectOwnerMixin(UserPassesTestMixin):
    """Restrict project mutations to owners and staff."""

    def test_func(self):
        """Return whether the current user owns the project."""
        return self.get_object().owner_id == self.request.user.id or self.request.user.is_staff


class ProjectUpdateView(LoginRequiredMixin, ProjectOwnerMixin, UpdateView):
    """Edit an owned project."""

    model = Project
    form_class = ProjectForm
    template_name = "projects/form.html"
    slug_url_kwarg = "slug"

    def form_valid(self, form):
        """Save the edit and show feedback."""
        messages.success(self.request, "Project updated.")
        return super().form_valid(form)


class ProjectDeleteView(LoginRequiredMixin, ProjectOwnerMixin, DeleteView):
    """Delete an owned project after confirmation."""

    model = Project
    template_name = "projects/confirm_delete.html"
    success_url = reverse_lazy("projects:list")
    slug_url_kwarg = "slug"

    def post(self, request, *args, **kwargs):
        """Delete the project and notify the owner."""
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Project deleted.")
        return response


class ProjectStatusView(LoginRequiredMixin, ProjectOwnerMixin, UpdateView):
    """Change a project between recruiting and completed."""

    model = Project
    form_class = ProjectStatusForm
    slug_url_kwarg = "slug"

    def post(self, request, *args, **kwargs):
        """Handle a status form as a POST-only action."""
        project = self.get_object()
        form = self.form_class(request.POST)
        if form.is_valid():
            project.status = form.cleaned_data["status"]
            project.save(update_fields=["status", "updated_at"])
            messages.success(request, "Project status updated.")
        else:
            messages.error(request, "Choose a valid project status.")
        return redirect(project)

    def get(self, request, *args, **kwargs):
        """Reject unsafe status GET requests."""
        from django.http import HttpResponse
        return HttpResponse("Method not allowed", status=405)


class ProjectUpdatePostView(LoginRequiredMixin, DetailView):
    """Post an update when the member is the project owner."""

    model = Project
    slug_url_kwarg = "slug"

    def post(self, request, *args, **kwargs):
        """Create an owner-authored update."""
        project = self.get_object()
        if project.owner_id != request.user.id and not request.user.is_staff:
            return redirect(project)
        form = ProjectUpdateForm(request.POST)
        if form.is_valid():
            ProjectUpdate.objects.create(project=project, author=request.user, **form.cleaned_data)
            messages.success(request, "Update posted.")
        return redirect(project)

    def get(self, request, *args, **kwargs):
        """Reject GET for this POST-only endpoint."""
        from django.http import HttpResponse
        return HttpResponse("Method not allowed", status=405)
