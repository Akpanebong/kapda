from django.urls import path
from . import views

app_name = "backups"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("run/", views.run_backup, name="run"),
    path("<pk_slug:pk>/download/", views.download_backup, name="download"),
    path("<pk_slug:pk>/restore/", views.restore_backup, name="restore"),
]
