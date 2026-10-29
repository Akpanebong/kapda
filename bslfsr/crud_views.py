from django.contrib.auth.decorators import login_required
from accounts.access import record_editor_required
from core.crud_support import create_record, delete_record, detail_record, list_records, update_record
from .forms import PeaceActivityForm
from .models import Beneficiary, FarmerRecord, PeaceActivity, PeaceCommittee, PeaceCommitteeMember, PeaceCommitteeMeeting

@login_required
def beneficiary_list(request): return list_records(request, Beneficiary, "bslfsr/beneficiary_list.html", "beneficiaries")
@login_required
def beneficiary_detail(request, pk): return detail_record(request, Beneficiary, pk, "bslfsr/beneficiary_detail.html")
@login_required
@record_editor_required
def beneficiary_create(request): return create_record(request, Beneficiary, "bslfsr/beneficiary_form.html", "bslfsr:beneficiary_list")
@login_required
@record_editor_required
def beneficiary_update(request, pk): return update_record(request, Beneficiary, pk, "bslfsr/beneficiary_form.html", "bslfsr:beneficiary_list")
@login_required
@record_editor_required
def beneficiary_delete(request, pk): return delete_record(request, Beneficiary, pk, "bslfsr:beneficiary_list")

@login_required
def farmer_record_list(request): return list_records(request, FarmerRecord, "bslfsr/farmer_record_list.html", "farmers")
@login_required
def farmer_record_detail(request, pk): return detail_record(request, FarmerRecord, pk, "bslfsr/farmer_record_detail.html")
@login_required
@record_editor_required
def farmer_record_create(request): return create_record(request, FarmerRecord, "bslfsr/farmer_record_form.html", "bslfsr:farmer_record_list")
@login_required
@record_editor_required
def farmer_record_update(request, pk): return update_record(request, FarmerRecord, pk, "bslfsr/farmer_record_form.html", "bslfsr:farmer_record_list")
@login_required
@record_editor_required
def farmer_record_delete(request, pk): return delete_record(request, FarmerRecord, pk, "bslfsr:farmer_record_list")

@login_required
def peace_activity_list(request): return list_records(request, PeaceActivity, "bslfsr/peace_activity_list.html", "peace_activities")
@login_required
def peace_activity_detail(request, pk): return detail_record(request, PeaceActivity, pk, "bslfsr/peace_activity_detail.html")
@login_required
@record_editor_required
def peace_activity_create(request): return create_record(request, PeaceActivity, "bslfsr/peace_activity_form.html", "bslfsr:peace_activity_list", PeaceActivityForm)
@login_required
@record_editor_required
def peace_activity_update(request, pk): return update_record(request, PeaceActivity, pk, "bslfsr/peace_activity_form.html", "bslfsr:peace_activity_list", PeaceActivityForm)
@login_required
@record_editor_required
def peace_activity_delete(request, pk): return delete_record(request, PeaceActivity, pk, "bslfsr:peace_activity_list")

@login_required
def peace_committee_list(request): return list_records(request, PeaceCommittee, "bslfsr/peace_committee_list.html", "peace_committees")
@login_required
def peace_committee_detail(request, pk): return detail_record(request, PeaceCommittee, pk, "bslfsr/peace_committee_detail.html")
@login_required
@record_editor_required
def peace_committee_create(request): return create_record(request, PeaceCommittee, "bslfsr/peace_committee_form.html", "bslfsr:peace_committee_list")
@login_required
@record_editor_required
def peace_committee_update(request, pk): return update_record(request, PeaceCommittee, pk, "bslfsr/peace_committee_form.html", "bslfsr:peace_committee_list")
@login_required
@record_editor_required
def peace_committee_delete(request, pk): return delete_record(request, PeaceCommittee, pk, "bslfsr:peace_committee_list")

@login_required
def peace_committee_member_list(request): return list_records(request, PeaceCommitteeMember, "bslfsr/peace_committee_member_list.html", "peace_committee_members")
@login_required
def peace_committee_member_detail(request, pk): return detail_record(request, PeaceCommitteeMember, pk, "bslfsr/peace_committee_member_detail.html")
@login_required
@record_editor_required
def peace_committee_member_create(request): return create_record(request, PeaceCommitteeMember, "bslfsr/peace_committee_member_form.html", "bslfsr:peace_committee_member_list")
@login_required
@record_editor_required
def peace_committee_member_update(request, pk): return update_record(request, PeaceCommitteeMember, pk, "bslfsr/peace_committee_member_form.html", "bslfsr:peace_committee_member_list")
@login_required
@record_editor_required
def peace_committee_member_delete(request, pk): return delete_record(request, PeaceCommitteeMember, pk, "bslfsr:peace_committee_member_list")

@login_required
def peace_committee_meeting_list(request): return list_records(request, PeaceCommitteeMeeting, "bslfsr/peace_committee_meeting_list.html", "peace_committee_meetings")
@login_required
def peace_committee_meeting_detail(request, pk): return detail_record(request, PeaceCommitteeMeeting, pk, "bslfsr/peace_committee_meeting_detail.html")
@login_required
@record_editor_required
def peace_committee_meeting_create(request): return create_record(request, PeaceCommitteeMeeting, "bslfsr/peace_committee_meeting_form.html", "bslfsr:peace_committee_meeting_list")
@login_required
@record_editor_required
def peace_committee_meeting_update(request, pk): return update_record(request, PeaceCommitteeMeeting, pk, "bslfsr/peace_committee_meeting_form.html", "bslfsr:peace_committee_meeting_list")
@login_required
@record_editor_required
def peace_committee_meeting_delete(request, pk): return delete_record(request, PeaceCommitteeMeeting, pk, "bslfsr:peace_committee_meeting_list")
