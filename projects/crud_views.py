from django.contrib.auth.decorators import login_required
from accounts.access import record_editor_required
from core.crud_support import create_record, delete_record, detail_record, list_records, update_record
from .models import ActivityData, Project

@login_required
def project_list(request): return list_records(request, Project, "projects/project_list.html", "projects")
@login_required
def project_detail(request, pk): return detail_record(request, Project, pk, "projects/project_detail.html")
@login_required
@record_editor_required
def project_create(request): return create_record(request, Project, "projects/project_form.html", "projects:project_list")
@login_required
@record_editor_required
def project_update(request, pk): return update_record(request, Project, pk, "projects/project_form.html", "projects:project_list")
@login_required
@record_editor_required
def project_delete(request, pk): return delete_record(request, Project, pk, "projects:project_list")

@login_required
def activity_data_list(request): return list_records(request, ActivityData, "projects/activity_data_list.html", "activity_data")
@login_required
def activity_data_detail(request, pk): return detail_record(request, ActivityData, pk, "projects/activity_data_detail.html")
@login_required
@record_editor_required
def activity_data_create(request): return create_record(request, ActivityData, "projects/activity_data_form.html", "projects:activity_data_list")
@login_required
@record_editor_required
def activity_data_update(request, pk): return update_record(request, ActivityData, pk, "projects/activity_data_form.html", "projects:activity_data_list")
@login_required
@record_editor_required
def activity_data_delete(request, pk): return delete_record(request, ActivityData, pk, "projects:activity_data_list")
