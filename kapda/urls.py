from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("data/", include("core.urls")),
    path("schools/", include("core.school_urls")),
    path("", include("reports.urls")),
    path("learners/", include("learners.urls")),
    path("projects/", include("projects.urls")),
    path("monitoring/", include("monitoring.urls")),
    path("governance/", include("school_governance.urls")),
    path("bslfsr/", include("bslfsr.urls")),
    path("vsla/", include("vsla_app.vsla.urls")),
    path("errors/", include("kapda.error_urls")),
]

handler400 = "kapda.error_views.custom_400_view"
handler403 = "kapda.error_views.custom_403_view"
handler404 = "kapda.error_views.custom_404_view"
handler500 = "kapda.error_views.custom_500_view"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
