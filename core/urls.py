"""Core URL routes."""

from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("team/", views.TeamView.as_view(), name="team"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("terms/", views.TermsView.as_view(), name="terms"),
    path("faq/", views.FaqView.as_view(), name="faq"),
    path("styleguide/", views.StyleguideView.as_view(), name="styleguide"),
    path("theme/", views.set_theme, name="set_theme"),
]
