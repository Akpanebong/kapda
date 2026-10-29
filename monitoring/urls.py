from django.urls import path
from .views import dashboard
from .crud_views import (field_visit_create, field_visit_delete, field_visit_detail, field_visit_list, field_visit_update,
                         follow_up_action_create, follow_up_action_delete, follow_up_action_detail, follow_up_action_list, follow_up_action_update,
                         mhm_session_create, mhm_session_delete, mhm_session_detail, mhm_session_list, mhm_session_update,
                         wash_facility_create, wash_facility_delete, wash_facility_detail, wash_facility_list, wash_facility_update)

app_name="monitoring"


urlpatterns=[
    path("",dashboard,name="activity_dashboard"),
    path("field-visits/", field_visit_list, name="field_visit_list"), path("field-visits/add/", field_visit_create, name="field_visit_create"), path("field-visits/<int:pk>/", field_visit_detail, name="field_visit_detail"), path("field-visits/<int:pk>/edit/", field_visit_update, name="field_visit_update"), path("field-visits/<int:pk>/delete/", field_visit_delete, name="field_visit_delete"),
    path("follow-up-actions/", follow_up_action_list, name="follow_up_action_list"), path("follow-up-actions/add/", follow_up_action_create, name="follow_up_action_create"), path("follow-up-actions/<int:pk>/", follow_up_action_detail, name="follow_up_action_detail"), path("follow-up-actions/<int:pk>/edit/", follow_up_action_update, name="follow_up_action_update"), path("follow-up-actions/<int:pk>/delete/", follow_up_action_delete, name="follow_up_action_delete"),
    path("mhm-sessions/", mhm_session_list, name="mhm_session_list"), path("mhm-sessions/add/", mhm_session_create, name="mhm_session_create"), path("mhm-sessions/<int:pk>/", mhm_session_detail, name="mhm_session_detail"), path("mhm-sessions/<int:pk>/edit/", mhm_session_update, name="mhm_session_update"), path("mhm-sessions/<int:pk>/delete/", mhm_session_delete, name="mhm_session_delete"),
    path("wash-facilities/", wash_facility_list, name="wash_facility_list"), path("wash-facilities/add/", wash_facility_create, name="wash_facility_create"), path("wash-facilities/<int:pk>/", wash_facility_detail, name="wash_facility_detail"), path("wash-facilities/<int:pk>/edit/", wash_facility_update, name="wash_facility_update"), path("wash-facilities/<int:pk>/delete/", wash_facility_delete, name="wash_facility_delete"),
]
