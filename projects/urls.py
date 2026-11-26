from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "projects"

urlpatterns = [
    path("projects/", RedirectView.as_view(pattern_name="discovery:search", permanent=False), name="list"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="create"),
    path("projects/mine", views.MyProjectsView.as_view(), name="mine"),
    path("projects/<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
    path("projects/<slug:slug>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
    path( "projects/<slug:slug>/delete/", views.ProjectDeleteView.as_view(), name="delete"),
]
