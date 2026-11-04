from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("projects/", views.ProjectListView.as_view(), name="list"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="create"),
    path("projects/<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
    path("projects/<slug:slug>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
]
