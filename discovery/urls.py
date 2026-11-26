"""Discovery URL routes."""

from django.urls import path
from . import views

app_name = "discovery"
urlpatterns = [
    path("search/", views.ProjectSearchView.as_view(), name="search"),
    path("people/", views.PeopleFinderView.as_view(), name="people"),
    path("recommended/", views.RecommendedProjectsView.as_view(), name="recommended"),
    path("skills/", views.MySkillsView.as_view(), name="skills"),
    path("skills/add/", views.UserSkillCreateView.as_view(), name="skill_add"),
    path("skills/<int:pk>/delete/", views.UserSkillDeleteView.as_view(), name="skill_delete"),
]
