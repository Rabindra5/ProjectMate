"""Project URL routes."""

from django.urls import path
from . import views

app_name = "projects"
urlpatterns = [
    path("projects/", views.ProjectListView.as_view(), name="list"),
    path("projects/mine/", views.MyProjectsView.as_view(), name="mine"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="create"),
    path("projects/<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
    path("projects/<slug:slug>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
    path("projects/<slug:slug>/delete/", views.ProjectDeleteView.as_view(), name="delete"),
    path("projects/<slug:slug>/status/", views.ProjectStatusView.as_view(), name="status"),
    path("projects/<slug:slug>/updates/new/", views.ProjectUpdatePostView.as_view(), name="update_post"),
]
