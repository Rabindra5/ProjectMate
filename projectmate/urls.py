"""Root URL configuration for ProjectMate."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("core.urls", "core"), namespace="core")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("", include(("discovery.urls", "discovery"), namespace="discovery")),
    path("", include(("projects.urls", "projects"), namespace="projects")),
    path("", include(("teams.urls", "teams"), namespace="teams")),
    path("", include(("activity.urls", "activity"), namespace="activity")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
