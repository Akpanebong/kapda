from django.urls import path
from .views import (activity_data_submit, indicator_create, indicator_delete,
                    indicator_detail, indicator_list, indicator_update,
                    monitoring_form_create, monitoring_form_delete,
                    monitoring_form_update, project_dashboard)
from .crud_views import (activity_data_create, activity_data_delete, activity_data_detail, activity_data_list,
                         activity_data_update, project_create, project_delete, project_detail, project_list, project_update)
app_name="projects"
urlpatterns=[
    path("",project_dashboard,name="project_dashboard"),
    path("manage/", project_list, name="project_list"),
    path("manage/add/", project_create, name="project_create"),
    path("manage/<int:pk>/", project_detail, name="project_detail"),
    path("manage/<int:pk>/edit/", project_update, name="project_update"),
    path("manage/<int:pk>/delete/", project_delete, name="project_delete"),
    path("activity-data/", activity_data_list, name="activity_data_list"),
    path("activity-data/add/", activity_data_create, name="activity_data_create"),
    path("activity-data/<int:pk>/", activity_data_detail, name="activity_data_detail"),
    path("activity-data/<int:pk>/edit/", activity_data_update, name="activity_data_update"),
    path("activity-data/<int:pk>/delete/", activity_data_delete, name="activity_data_delete"),
    path("activities/<int:pk>/data/", activity_data_submit, name="activity_data_submit"),
    path("indicators/", indicator_list, name="indicator_list"),
    path("indicators/add/", indicator_create, name="indicator_create"),
    path("indicators/<int:pk>/", indicator_detail, name="indicator_detail"),
    path("indicators/<int:pk>/edit/", indicator_update, name="indicator_update"),
    path("indicators/<int:pk>/delete/", indicator_delete, name="indicator_delete"),
    path("indicators/<int:indicator_id>/monitoring-form/add/", monitoring_form_create, name="monitoring_form_create"),
    path("indicators/<int:indicator_id>/monitoring-form/edit/", monitoring_form_update, name="monitoring_form_update"),
    path("indicators/<int:indicator_id>/monitoring-form/delete/", monitoring_form_delete, name="monitoring_form_delete"),
]
