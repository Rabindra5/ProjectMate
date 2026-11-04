"""Project views."""

from django.views.generic import ListView, CreateView, DetailView
from .models import Project
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ProjectForm


class ProjectListView(ListView):
    """Display projects ordered by newest first."""

    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"
    paginate_by = 9

    def get_queryset(self):
        return (
            Project.objects
            .select_related("owner", "category")
            .prefetch_related("required_skills")
        )



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



class ProjectDetailView(DetailView):
    """Show a project and its public collaboration details."""

    model = Project
    slug_url_kwarg = "slug"
    template_name = "projects/detail.html"

    def get_queryset(self):
        """Avoid N+1 queries for project cards."""
        return Project.objects.select_related(
            "owner", "category"
        ).prefetch_related(
            "required_skills", "updates__author"
        )
