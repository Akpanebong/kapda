from django.contrib.auth.decorators import login_required
from accounts.access import record_editor_required
from core.crud_support import create_record, delete_record, detail_record, list_records, update_record
from .models import FieldVisit, FollowUpAction, MHMSession, WASHFacility

@login_required
def field_visit_list(request): return list_records(request, FieldVisit, "monitoring/field_visit_list.html", "field_visits")
@login_required
def field_visit_detail(request, pk): return detail_record(request, FieldVisit, pk, "monitoring/field_visit_detail.html")
@login_required
@record_editor_required
def field_visit_create(request): return create_record(request, FieldVisit, "monitoring/field_visit_form.html", "monitoring:field_visit_list")
@login_required
@record_editor_required
def field_visit_update(request, pk): return update_record(request, FieldVisit, pk, "monitoring/field_visit_form.html", "monitoring:field_visit_list")
@login_required
@record_editor_required
def field_visit_delete(request, pk): return delete_record(request, FieldVisit, pk, "monitoring:field_visit_list")

@login_required
def follow_up_action_list(request): return list_records(request, FollowUpAction, "monitoring/follow_up_action_list.html", "follow_up_actions")
@login_required
def follow_up_action_detail(request, pk): return detail_record(request, FollowUpAction, pk, "monitoring/follow_up_action_detail.html")
@login_required
@record_editor_required
def follow_up_action_create(request): return create_record(request, FollowUpAction, "monitoring/follow_up_action_form.html", "monitoring:follow_up_action_list")
@login_required
@record_editor_required
def follow_up_action_update(request, pk): return update_record(request, FollowUpAction, pk, "monitoring/follow_up_action_form.html", "monitoring:follow_up_action_list")
@login_required
@record_editor_required
def follow_up_action_delete(request, pk): return delete_record(request, FollowUpAction, pk, "monitoring:follow_up_action_list")

@login_required
def mhm_session_list(request): return list_records(request, MHMSession, "monitoring/mhm_session_list.html", "mhm_sessions")
@login_required
def mhm_session_detail(request, pk): return detail_record(request, MHMSession, pk, "monitoring/mhm_session_detail.html")
@login_required
@record_editor_required
def mhm_session_create(request): return create_record(request, MHMSession, "monitoring/mhm_session_form.html", "monitoring:mhm_session_list")
@login_required
@record_editor_required
def mhm_session_update(request, pk): return update_record(request, MHMSession, pk, "monitoring/mhm_session_form.html", "monitoring:mhm_session_list")
@login_required
@record_editor_required
def mhm_session_delete(request, pk): return delete_record(request, MHMSession, pk, "monitoring:mhm_session_list")

@login_required
def wash_facility_list(request): return list_records(request, WASHFacility, "monitoring/wash_facility_list.html", "wash_facilities")
@login_required
def wash_facility_detail(request, pk): return detail_record(request, WASHFacility, pk, "monitoring/wash_facility_detail.html")
@login_required
@record_editor_required
def wash_facility_create(request): return create_record(request, WASHFacility, "monitoring/wash_facility_form.html", "monitoring:wash_facility_list")
@login_required
@record_editor_required
def wash_facility_update(request, pk): return update_record(request, WASHFacility, pk, "monitoring/wash_facility_form.html", "monitoring:wash_facility_list")
@login_required
@record_editor_required
def wash_facility_delete(request, pk): return delete_record(request, WASHFacility, pk, "monitoring:wash_facility_list")
