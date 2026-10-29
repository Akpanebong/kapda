from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from accounts.access import record_editor_required
from core.crud_support import create_record, delete_record, detail_record, list_records, update_record
from .forms import AttendanceRecordForm, LearnerSupportForm
from .models import Assessment, AttendanceRecord, ClassMovement, Enrolment, Learner, LearnerProject, LearnerStatusHistory, UNEBResult
from .models import LearnerSupport

@login_required
def learner_project_list(request): return list_records(request, LearnerProject, "learners/learner_project_list.html", "learner_projects")
@login_required
def learner_project_detail(request, pk): return detail_record(request, LearnerProject, pk, "learners/learner_project_detail.html")
@login_required
@record_editor_required
def learner_project_create(request): return create_record(request, LearnerProject, "learners/learner_project_form.html", "learners:learner_project_list")
@login_required
@record_editor_required
def learner_project_update(request, pk): return update_record(request, LearnerProject, pk, "learners/learner_project_form.html", "learners:learner_project_list")
@login_required
@record_editor_required
def learner_project_delete(request, pk): return delete_record(request, LearnerProject, pk, "learners:learner_project_list")

@login_required
def enrolment_list(request): return list_records(request, Enrolment, "learners/enrolment_list.html", "enrolments")
@login_required
def enrolment_detail(request, pk): return detail_record(request, Enrolment, pk, "learners/enrolment_detail.html")
@login_required
@record_editor_required
def enrolment_record_create(request): return create_record(request, Enrolment, "learners/enrolment_form.html", "learners:enrolment_list")
@login_required
@record_editor_required
def enrolment_record_update(request, pk): return update_record(request, Enrolment, pk, "learners/enrolment_form.html", "learners:enrolment_list")
@login_required
@record_editor_required
def enrolment_record_delete(request, pk): return delete_record(request, Enrolment, pk, "learners:enrolment_list")

@login_required
def attendance_record_list(request):
    records = AttendanceRecord.objects.select_related(
        "learner", "enrolment", "enrolment__school", "term", "term__academic_year"
    ).order_by("-term__academic_year__start_date", "-term__start_date", "learner__last_name")

    school_id = request.GET.get("school", "")
    class_level = request.GET.get("class", "")
    term_id = request.GET.get("term", "")
    learner_id = request.GET.get("learner", "")

    if school_id:
        records = records.filter(enrolment__school_id=school_id)
    if class_level:
        records = records.filter(enrolment__class_level=class_level)
    if term_id:
        records = records.filter(term_id=term_id)
    if learner_id:
        records = records.filter(learner_id=learner_id)

    page = Paginator(records, 25).get_page(request.GET.get("page"))
    from core.models import School, Term
    class_levels = [value for value, label in Enrolment._meta.get_field("class_level").choices]
    return render(request, "learners/attendance_list.html", {
        "attendance_records": page,
        "schools": School.objects.order_by("name"),
        "terms": Term.objects.select_related("academic_year").order_by("-academic_year__start_date", "start_date"),
        "class_levels": class_levels,
        "selected_school": school_id,
        "selected_class": class_level,
        "selected_term": term_id,
        "selected_learner": learner_id,
    })
@login_required
def attendance_record_detail(request, pk): return detail_record(request, AttendanceRecord, pk, "learners/attendance_detail.html")
@login_required
@record_editor_required
def attendance_record_create(request):
    learner_id = request.GET.get("learner") or request.POST.get("learner_context")
    learner = get_object_or_404(Learner, pk=learner_id) if learner_id else None
    return create_record(
        request,
        AttendanceRecord,
        "learners/attendance_form.html",
        "learners:attendance_record_list",
        AttendanceRecordForm,
        {"learner": learner},
    )
@login_required
@record_editor_required
def attendance_record_update(request, pk): return update_record(request, AttendanceRecord, pk, "learners/attendance_form.html", "learners:attendance_record_list")
@login_required
@record_editor_required
def attendance_record_delete(request, pk): return delete_record(request, AttendanceRecord, pk, "learners:attendance_record_list")

def _crud(model, name, template):
    return (lambda request: list_records(request, model, f"learners/{template}_list.html", name),
            lambda request, pk: detail_record(request, model, pk, f"learners/{template}_detail.html"),
            lambda request: create_record(request, model, f"learners/{template}_form.html", f"learners:{name}_list"),
            lambda request, pk: update_record(request, model, pk, f"learners/{template}_form.html", f"learners:{name}_list"),
            lambda request, pk: delete_record(request, model, pk, f"learners:{name}_list"))

def _export(name, model, template):
    views = _crud(model, name, template)
    globals()[f"{name}_list"] = login_required(views[0]); globals()[f"{name}_detail"] = login_required(views[1])
    globals()[f"{name}_create"] = record_editor_required(login_required(views[2])); globals()[f"{name}_update"] = record_editor_required(login_required(views[3])); globals()[f"{name}_delete"] = record_editor_required(login_required(views[4]))

_export("class_movement", ClassMovement, "class_movement")
_export("assessment", Assessment, "assessment")
_export("uneb_result", UNEBResult, "uneb_result")
_export("learner_status_history", LearnerStatusHistory, "learner_status_history")

@login_required
def learner_support_list(request): return list_records(request, LearnerSupport, "learners/learner_support_list.html", "learner_support")
@login_required
def learner_support_detail(request, pk): return detail_record(request, LearnerSupport, pk, "learners/learner_support_detail.html")
@login_required
@record_editor_required
def learner_support_record_create(request): return create_record(request, LearnerSupport, "learners/learner_support_form.html", "learners:learner_support_list", LearnerSupportForm)
@login_required
@record_editor_required
def learner_support_record_update(request, pk): return update_record(request, LearnerSupport, pk, "learners/learner_support_form.html", "learners:learner_support_list", LearnerSupportForm)
@login_required
@record_editor_required
def learner_support_record_delete(request, pk): return delete_record(request, LearnerSupport, pk, "learners:learner_support_list")
