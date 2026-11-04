from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("projects/", views.ProjectListView.as_view(), name="list"),
]