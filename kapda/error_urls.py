from django.urls import path

from .error_views import report_500_error

app_name = "errors"
urlpatterns = [path("report/", report_500_error, name="report")]

