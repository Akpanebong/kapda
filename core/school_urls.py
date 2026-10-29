from django.urls import path
from . import school_views

app_name = "schools"
urlpatterns = [path("", school_views.school_list, name="list")]
