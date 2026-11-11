from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.access import record_editor_required
from core.crud_support import create_record, delete_record, detail_record, list_records, update_record
from .models import ActivityData, Project
from .forms import ActivityDataCaptureForm, ActivityDataReviewForm

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
def activity_data_review(request, pk):
    record = get_object_or_404(
        ActivityData.objects.select_related("activity", "project", "entered_by", "verified_by"),
        pk=pk,
    )
    form = ActivityDataReviewForm(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        reviewed_record = form.save(commit=False)
        reviewed_record.verified_by = request.user
        reviewed_record.save(update_fields=["verification_status", "comments", "verified_by", "updated_at"])
        messages.success(request, "Activity data review saved successfully.")
        return redirect("projects:activity_data_detail", pk=record)
    return render(request, "projects/activity_data_review.html", {"object": record, "form": form})

@login_required
@record_editor_required
def activity_data_create(request): return create_record(request, ActivityData, "projects/activity_data_form.html", "projects:activity_data_list", form_class=ActivityDataCaptureForm)
@login_required
@record_editor_required
def activity_data_update(request, pk): return update_record(request, ActivityData, pk, "projects/activity_data_form.html", "projects:activity_data_list", form_class=ActivityDataCaptureForm)
@login_required
@record_editor_required
def activity_data_delete(request, pk): return delete_record(request, ActivityData, pk, "projects:activity_data_list")
