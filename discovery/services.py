"""Reusable project search and matching logic."""

from django.db.models import Case, Count, IntegerField, Q, When, F, Value, ExpressionWrapper
from projects.models import Project


def filter_projects(queryset, cleaned_data, user=None):
    """Apply every validated project filter and keyword term."""
    query = (cleaned_data.get("q") or "").strip()
    for term in query.split():
        queryset = queryset.filter(
            Q(title__icontains=term) | Q(summary__icontains=term) | Q(description__icontains=term)
            | Q(category__name__icontains=term) | Q(required_skills__name__icontains=term)
            | Q(owner__username__icontains=term) | Q(owner__first_name__icontains=term) | Q(owner__last_name__icontains=term)
        )
    if cleaned_data.get("category"):
        queryset = queryset.filter(category=cleaned_data["category"])
    if cleaned_data.get("project_type"):
        queryset = queryset.filter(project_type=cleaned_data["project_type"])
    if cleaned_data.get("status"):
        queryset = queryset.filter(status=cleaned_data["status"])
    if cleaned_data.get("skill"):
        queryset = queryset.filter(required_skills=cleaned_data["skill"])
    return queryset.distinct().select_related("owner", "category").prefetch_related("required_skills")


def annotate_match(queryset, user):
    """Annotate projects with required-skill match percentages."""
    skill_ids = user.user_skills.values_list("skill_id", flat=True)
    queryset = queryset.annotate(
        matched=Count("required_skills", filter=Q(required_skills__in=skill_ids), distinct=True),
        required=Count("required_skills", distinct=True),
    )
    return queryset.annotate(match_pct=Case(When(required=0, then=Value(None)), default=ExpressionWrapper(F("matched") * 100 / F("required"), output_field=IntegerField())))


def get_similar_projects(project, limit=4):
    """Recommend available projects with similar categories and skills."""
    from django.db.models.functions import Greatest

    skill_ids = list(
        project.required_skills.values_list("pk", flat=True)
    )

    return (
        Project.objects.filter(status="recruiting")
        .exclude(pk=project.pk)
        .annotate(
            shared_skills=Count(
                "required_skills",
                filter=Q(required_skills__in=skill_ids),
                distinct=True,
            ),
            category_match=Case(
                When(category_id=project.category_id, then=Value(3)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            available_slots=Greatest(
                F("max_members") - Count("memberships", distinct=True),
                Value(0),
            ),
        )
        .annotate(
            similarity_score=F("shared_skills") * 2 + F("category_match")
        )
        .filter(similarity_score__gt=0, available_slots__gt=0)
        .select_related("category", "owner")
        .prefetch_related("required_skills")
        .order_by("-similarity_score", "-created_at", "-pk")[:limit]
    )
