from django.urls import path
from . import views

app_name = "governance"
urlpatterns = [
    path("", views.governance_dashboard, name="governance_dashboard"),
    path("members/", views.governance_member_list, name="governance_member_list"),
    path("members/add/", views.governance_member_create, name="governance_member_create"),
    path("members/<pk_slug:pk>/edit/", views.governance_member_update, name="governance_member_update"),
    path("members/<pk_slug:pk>/delete/", views.governance_member_delete, name="governance_member_delete"),
    path("meetings/", views.governance_meeting_list, name="governance_meeting_list"),
    path("meetings/add/", views.governance_meeting_create, name="governance_meeting_create"),
    path("meetings/<pk_slug:pk>/edit/", views.governance_meeting_update, name="governance_meeting_update"),
    path("meetings/<pk_slug:pk>/delete/", views.governance_meeting_delete, name="governance_meeting_delete"),
    path("training/", views.governance_training_list, name="governance_training_list"),
    path("training/add/", views.governance_training_create, name="governance_training_create"),
    path("training/<pk_slug:pk>/edit/", views.governance_training_update, name="governance_training_update"),
    path("training/<pk_slug:pk>/delete/", views.governance_training_delete, name="governance_training_delete"),
    path("plans/", views.school_improvement_plan_list, name="school_improvement_plan_list"),
    path("plans/add/", views.school_improvement_plan_create, name="school_improvement_plan_create"),
    path("plans/<pk_slug:pk>/edit/", views.school_improvement_plan_update, name="school_improvement_plan_update"),
    path("plans/<pk_slug:pk>/delete/", views.school_improvement_plan_delete, name="school_improvement_plan_delete"),
    path("actions/", views.governance_action_list, name="governance_action_list"),
    path("actions/add/", views.governance_action_create, name="governance_action_create"),
    path("actions/<pk_slug:pk>/edit/", views.governance_action_update, name="governance_action_update"),
    path("actions/<pk_slug:pk>/delete/", views.governance_action_delete, name="governance_action_delete"),
]
