"""Discovery, search, and skill views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView
from activity.services import record_search
from accounts.models import Profile
from projects.models import Project
from .forms import PeopleSearchForm, ProjectSearchForm, UserSkillForm
from .models import UserSkill
from .services import annotate_match, filter_projects


class ProjectSearchView(ListView):
    """Search and filter projects for guests and members."""

    model = Project
    template_name = "discovery/search.html"
    context_object_name = "projects"
    paginate_by = 9

    def get_queryset(self):
        """Apply validated filters and a safe sort."""
        self.form = ProjectSearchForm(self.request.GET)
        queryset = Project.objects.all()
        if self.form.is_valid():
            data = self.form.cleaned_data
            queryset = filter_projects(queryset, data, self.request.user)
            if data.get("sort") == "deadline":
                queryset = queryset.order_by("deadline", "-created_at")
            elif data.get("sort") == "best_match" and self.request.user.is_authenticated:
                queryset = annotate_match(queryset, self.request.user).order_by("-match_pct", "-created_at")
            if any(data.values()):
                record_search(self.request, self.request.GET)
        return queryset

    def get_context_data(self, **kwargs):
        """Expose the filter form."""
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context


class PeopleFinderView(LoginRequiredMixin, ListView):
    """Find opted-in student profiles by name or skill."""

    model = Profile
    template_name = "discovery/people.html"
    context_object_name = "people"

    def get_queryset(self):
        """Exclude the viewer and opted-out students."""
        self.form = PeopleSearchForm(self.request.GET)
        queryset = Profile.objects.filter(open_to_teams=True, user__is_active=True).exclude(user=self.request.user).select_related("user").prefetch_related("user__user_skills__skill")
        if self.form.is_valid():
            data = self.form.cleaned_data
            if data.get("q"):
                query = data["q"]
                queryset = queryset.filter(Q(user__username__icontains=query) | Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) | Q(headline__icontains=query) | Q(program__icontains=query))
            if data.get("skill"):
                queryset = queryset.filter(user__user_skills__skill=data["skill"])
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        """Expose the people filter form."""
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context


class RecommendedProjectsView(LoginRequiredMixin, ListView):
    """Recommend recruiting projects not already joined."""

    model = Project
    template_name = "discovery/recommended.html"
    context_object_name = "projects"

    def get_queryset(self):
        """Rank open projects by skill match."""
        joined = Project.objects.filter(memberships__user=self.request.user)
        return annotate_match(Project.objects.filter(status="recruiting").exclude(owner=self.request.user).exclude(pk__in=joined), self.request.user).order_by("-match_pct", "-created_at")[:6]


class MySkillsView(LoginRequiredMixin, ListView):
    """List the current user's skills."""

    model = UserSkill
    template_name = "discovery/my_skills.html"
    context_object_name = "skills"

    def get_queryset(self):
        """Load skill names in one query."""
        return UserSkill.objects.filter(user=self.request.user).select_related("skill")


class UserSkillCreateView(LoginRequiredMixin, CreateView):
    """Add a skill to the current profile."""

    model = UserSkill
    form_class = UserSkillForm
    template_name = "discovery/skill_form.html"

    def get_form_kwargs(self):
        """Pass the current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Set ownership from the session."""
        form.instance.user = self.request.user
        messages.success(self.request, "Skill added.")
        return super().form_valid(form)

    def get_success_url(self):
        """Return to the skills list."""
        return reverse_lazy("discovery:skills")


class UserSkillDeleteView(LoginRequiredMixin, DeleteView):
    """Delete only the current user's skill assignment."""

    model = UserSkill
    success_url = reverse_lazy("discovery:skills")

    def get_queryset(self):
        """Prevent IDOR by scoping to the current user."""
        return UserSkill.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        """Delete the assignment with feedback."""
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Skill removed.")
        return response

    def get(self, request, *args, **kwargs):
        """Reject unsafe skill deletion GET requests."""
        from django.http import HttpResponse
        return HttpResponse("Method not allowed", status=405)
