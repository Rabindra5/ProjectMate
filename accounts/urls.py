"""Account URL routes."""

from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("profile/links/add/", views.ProfileLinkCreateView.as_view(), name="profile_link_add"),
    path("profile/links/<int:pk>/delete/", views.ProfileLinkDeleteView.as_view(), name="profile_link_delete"),
    path("password-change/", views.PasswordChange, name="password_change"),
    path("password-change/done/", views.PasswordChangeDone, name="password_change_done"),
    path("password-reset/", views.PasswordReset, name="password_reset"),
    path("password-reset/done/", views.PasswordResetDone, name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/", views.PasswordResetConfirm, name="password_reset_confirm"),
    path("password-reset/complete/", views.PasswordResetComplete, name="password_reset_complete"),
    path("u/<str:username>/", views.ProfileDetailView.as_view(), name="profile"),
]
