"""Discovery, search, and skill views."""

from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.db.models.functions import Greatest
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import CreateView, DeleteView, ListView, FormView

from accounts.models import Profile
from activity.services import record_search
from projects.models import Project

from .forms import PeopleSearchForm, ProjectSearchForm, UserSkillForm, ManageSkillsForm
from .models import Skill, UserSkill
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
        projects = projects.annotate(
            available_slots=Greatest(
                F("max_members") - Count("memberships", distinct=True),
                Value(0),
            )
        ).filter(available_slots__gt=0)

        return annotate_match(projects, user).filter(
            matched__gt=0
        ).select_related(
            "owner", "category"
        ).prefetch_related(
            "required_skills"
        ).order_by(
            "-match_pct", "-matched", "-created_at", "-pk"
        )[:6]


class MySkillsView(LoginRequiredMixin, FormView):
    """Manage the current user's selected skills."""

    template_name = "discovery/my_skills.html"
    form_class = ManageSkillsForm
    success_url = reverse_lazy("discovery:skills")

    def get_initial(self):
        return {
            "skills": list(
                self.request.user.user_skills.values_list(
                    "skill_id", flat=True
                )
            )
        }

    @transaction.atomic
    def form_valid(self, form):
        user = self.request.user
        selected = set(
            form.cleaned_data["skills"].values_list("pk", flat=True)
        )

        new_name = form.cleaned_data["new_skill"].strip()

        if self.request.POST.get("action") == "add":
            if not new_name:
                form.add_error("new_skill", "Enter a skill name.")
                return self.form_invalid(form)

            skill = Skill.objects.filter(name__iexact=new_name).first()

            if len(selected) >= 25 and (
                skill is None or skill.pk not in selected
            ):
                form.add_error("new_skill", "You can select up to 25 skills.")
                return self.form_invalid(form)

            if skill is None:
                base = slugify(new_name) or "skill"
                slug = base
                number = 1

                while Skill.objects.filter(slug=slug).exists():
                    slug = f"{base}-{number}"
                    number += 1

                skill = Skill.objects.create(
                    name=new_name,
                    slug=slug,
                    group="tools",
                )

            data = self.request.POST.copy()
            data.setlist("skills", [
                str(pk) for pk in selected | {skill.pk}
            ])
            data["new_skill"] = ""

            updated_form = self.form_class(data=data)
            return self.render_to_response(
                self.get_context_data(form=updated_form)
            )

        if new_name:
            form.add_error("new_skill", "Click Add skill before saving.")
            return self.form_invalid(form)

        UserSkill.objects.filter(user=user).exclude(
            skill_id__in=selected
        ).delete()

        for skill_id in selected:
            UserSkill.objects.get_or_create(
                user=user,
                skill_id=skill_id,
                defaults={"proficiency": 1}
            )

        messages.success(self.request, "Skills saved successfully.")
        return super().form_valid(form)


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