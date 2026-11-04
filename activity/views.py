"""History and project resource views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView
from projects.models import Project
from teams.models import Membership
from .forms import HistoryFilterForm, ResourceUploadForm
from .models import ProjectResource, SiteVisit, ViewedProject


def is_member(user, project):
    """Return whether a user may access team resources."""
    return user.is_staff or Membership.objects.filter(project=project, user=user).exists()


class HistoryDashboardView(LoginRequiredMixin, TemplateView):
    """Show member visits, recent projects, and searches."""

    template_name = "activity/history.html"

    def get_context_data(self, **kwargs):
        """Load bounded history data."""
        context = super().get_context_data(**kwargs)
        context["viewed_projects"] = ViewedProject.objects.filter(user=self.request.user).select_related("project")[:10]
        context["uploads"] = ProjectResource.objects.filter(uploaded_by=self.request.user).select_related("project")[:10]
        context["visits_today"] = SiteVisit.objects.filter(user=self.request.user).order_by("-date").first()
        context["recent_searches"] = self.request.session.get("recent_searches", [])
        return context


class ClearHistoryView(LoginRequiredMixin, TemplateView):
    """Clear member and session history with POST."""

    def post(self, request, *args, **kwargs):
        """Delete history rows and session lists."""
        ViewedProject.objects.filter(user=request.user).delete()
        request.session["recent_projects"] = []
        request.session["recent_searches"] = []
        messages.success(request, "Your activity history was cleared.")
        return redirect("activity:history")

    def get(self, request, *args, **kwargs):
        """Reject GET for history deletion."""
        from django.http import HttpResponse
        return HttpResponse("Method not allowed", status=405)


class ResourceListView(LoginRequiredMixin, ListView):
    """List resources visible to a project member."""

    model = ProjectResource
    template_name = "activity/resources.html"
    context_object_name = "resources"

    def get_queryset(self):
        """Limit private resources to project members."""
        project = get_object_or_404(Project, slug=self.kwargs["slug"])
        if not is_member(self.request.user, project):
            return ProjectResource.objects.filter(project=project, is_public=True)
        return ProjectResource.objects.filter(project=project)

    def get_context_data(self, **kwargs):
        """Add the project context."""
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, slug=self.kwargs["slug"])
        return context


class ResourceUploadView(LoginRequiredMixin, CreateView):
    """Upload a resource as a project member."""

    model = ProjectResource
    form_class = ResourceUploadForm
    template_name = "activity/resource_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Require membership before showing the form."""
        self.project = get_object_or_404(Project, slug=kwargs["slug"])
        if not is_member(request.user, self.project):
            return redirect(self.project)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Record server-side upload metadata."""
        form.instance.project = self.project
        form.instance.uploaded_by = self.request.user
        form.instance.original_name = form.instance.file.name[:255]
        form.instance.size_bytes = form.instance.file.size
        form.instance.content_type = getattr(form.instance.file, "content_type", "application/octet-stream")
        messages.success(self.request, "Resource uploaded.")
        return super().form_valid(form)

    def get_success_url(self):
        """Return to the resource list."""
        return reverse_lazy("activity:resources", kwargs={"slug": self.project.slug})


class ResourceDownloadView(LoginRequiredMixin, ListView):
    """Download only a resource visible to the current user."""

    def get(self, request, *args, **kwargs):
        """Return an attachment or a friendly 404."""
        resource = get_object_or_404(ProjectResource.objects.select_related("project"), pk=kwargs["pk"])
        if not resource.is_public and not is_member(request.user, resource.project):
            raise Http404
        if not resource.file:
            raise Http404
        try:
            return FileResponse(resource.file.open("rb"), as_attachment=True, filename=resource.original_name)
        except FileNotFoundError as exc:
            raise Http404 from exc


class ResourceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a resource by its uploader or project owner."""

    model = ProjectResource

    def get_queryset(self):
        """Scope deletion to permitted users."""
        return ProjectResource.objects.filter(project__owner=self.request.user) | ProjectResource.objects.filter(uploaded_by=self.request.user)

    def post(self, request, *args, **kwargs):
        """Delete the file and show feedback."""
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Resource deleted.")
        return response

    def get(self, request, *args, **kwargs):
        """Reject unsafe resource deletion GET requests."""
        from django.http import HttpResponse
        return HttpResponse("Method not allowed", status=405)

    def get_success_url(self):
        """Return to the project resources."""
        return reverse_lazy("activity:resources", kwargs={"slug": self.object.project.slug})
