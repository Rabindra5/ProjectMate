"""Discovery, search, and skill views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.db.models.functions import Greatest
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

from accounts.models import Profile
from activity.services import record_search
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
        self.form = ProjectSearchForm(self.request.GET)
        queryset = Project.objects.all()

        if self.form.is_valid():
            data = self.form.cleaned_data
            queryset = filter_projects(queryset, data, self.request.user)
            sort = data.get("sort")

            if sort == "deadline":
                queryset = queryset.order_by("deadline", "-created_at")
            elif sort == "best_match" and self.request.user.is_authenticated:
                queryset = annotate_match(queryset, self.request.user).order_by(
                    "-match_pct", "-created_at"
                )
            elif sort == "open_slots":
                queryset = queryset.annotate(
                    available_slots=Case(
                        When(
                            status="recruiting",
                            then=Greatest(
                                F("max_members") - Count("memberships", distinct=True),
                                Value(0),
                            ),
                        ),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ).filter(available_slots__gt=0).order_by("-available_slots", "-created_at", "-pk")

            if any(data.values()):
                record_search(self.request, self.request.GET)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context


class PeopleFinderView(LoginRequiredMixin, ListView):
    """Find opted-in student profiles by name or skill."""

    model = Profile
    template_name = "discovery/people.html"
    context_object_name = "people"

    def get_queryset(self):
        self.form = PeopleSearchForm(self.request.GET)
        queryset = (
            Profile.objects.filter(open_to_teams=True, user__is_active=True)
            .exclude(user=self.request.user)
            .select_related("user")
            .prefetch_related("user__user_skills__skill")
        )

        if self.form.is_valid():
            data = self.form.cleaned_data
            if data.get("q"):
                query = data["q"]
                queryset = queryset.filter(
                    Q(user__username__icontains=query)
                    | Q(user__first_name__icontains=query)
                    | Q(user__last_name__icontains=query)
                    | Q(headline__icontains=query)
                    | Q(program__icontains=query)
                )
            if data.get("skill"):
                queryset = queryset.filter(user__user_skills__skill=data["skill"])

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context


class RecommendedProjectsView(LoginRequiredMixin, ListView):
    """Recommend recruiting projects the member has not joined."""

    model = Project
    template_name = "discovery/recommended.html"
    context_object_name = "projects"

    def get_queryset(self):
        user = self.request.user
        joined = Project.objects.filter(memberships__user=user)
        projects = (
            Project.objects.filter(status="recruiting")
            .exclude(owner=user)
            .exclude(pk__in=joined)
        )
        return annotate_match(projects, user).order_by(
            "-match_pct", "-created_at"
        )[:6]


class MySkillsView(LoginRequiredMixin, ListView):
    """List the current user's skills."""

    model = UserSkill
    template_name = "discovery/my_skills.html"
    context_object_name = "skills"

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user).select_related("skill")


class UserSkillCreateView(LoginRequiredMixin, CreateView):
    """Add a skill to the current user's profile."""

    model = UserSkill
    form_class = UserSkillForm
    template_name = "discovery/skill_form.html"
    success_url = reverse_lazy("discovery:skills")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Skill added.")
        return response


class UserSkillDeleteView(LoginRequiredMixin, DeleteView):
    """Delete only a skill assignment owned by the current user."""

    model = UserSkill
    success_url = reverse_lazy("discovery:skills")

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Skill removed.")
        return response

    def get(self, request, *args, **kwargs):
        return HttpResponse("Method not allowed", status=405)