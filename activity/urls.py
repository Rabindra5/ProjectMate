"""Activity URL routes."""

from django.urls import path
from . import views

app_name = "activity"
urlpatterns = [
    path("activity/", views.HistoryDashboardView.as_view(), name="history"),
    path("activity/clear/", views.ClearHistoryView.as_view(), name="clear"),
    path("projects/<slug:slug>/resources/", views.ResourceListView.as_view(), name="resources"),
    path("projects/<slug:slug>/resources/upload/", views.ResourceUploadView.as_view(), name="resource_upload"),
    path("resources/<int:pk>/download/", views.ResourceDownloadView.as_view(), name="resource_download"),
    path("resources/<int:pk>/delete/", views.ResourceDeleteView.as_view(), name="resource_delete"),
]
