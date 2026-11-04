"""Team URL routes."""

from django.urls import path
from . import views

app_name = "teams"
urlpatterns = [
    path("projects/<slug:slug>/apply/", views.JoinRequestCreateView.as_view(), name="apply"),
    path("projects/<slug:slug>/team/", views.TeamDetailView.as_view(), name="team"),
    path("projects/<slug:slug>/leave/", views.LeaveProjectView.as_view(), name="leave"),
    path("projects/<slug:slug>/members/<int:pk>/remove/", views.RemoveMemberView.as_view(), name="remove_member"),
    path("requests/", views.MySentRequestsView.as_view(), name="my_requests"),
    path("requests/inbox/", views.OwnerInboxView.as_view(), name="request_inbox"),
    path("requests/<int:pk>/decide/", views.DecisionView.as_view(), name="decide"),
    path("requests/<int:pk>/withdraw/", views.WithdrawView.as_view(), name="withdraw"),
]
