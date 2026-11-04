"""Project views."""

from django.views.generic import ListView
from .models import Project
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
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
