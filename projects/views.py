"""Project views."""

from django.views.generic import ListView
from .models import Project


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