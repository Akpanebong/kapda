from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from types import SimpleNamespace
from accounts.access import record_editor_required
from core.crud_support import create_record, delete_record, detail_record, list_records, update_record
from .forms import (
    AssessmentDetailsForm,
    AssessmentSubjectFormSet,
    AttendanceRecordForm,
    LearnerSupportForm,
    UNEBResultForm,
    UNEBSubjectFormSet,
)
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

def _export(name, model, template, context_name=None):
    views = _crud(model, name, template)
    list_view = lambda request: list_records(request, model, f"learners/{template}_list.html", context_name or name)
    globals()[f"{name}_list"] = login_required(list_view); globals()[f"{name}_detail"] = login_required(views[1])
    globals()[f"{name}_create"] = record_editor_required(login_required(views[2])); globals()[f"{name}_update"] = record_editor_required(login_required(views[3])); globals()[f"{name}_delete"] = record_editor_required(login_required(views[4]))

_export("class_movement", ClassMovement, "class_movement")
_export("assessment", Assessment, "assessment", "assessments")
_export("uneb_result", UNEBResult, "uneb_result", "uneb_results")
_export("learner_status_history", LearnerStatusHistory, "learner_status_history")


def _assessment_groups(queryset):
    grouped = {}
    for assessment in queryset:
        key = (assessment.learner_id, assessment.enrolment_id, assessment.term_id)
        if key not in grouped:
            grouped[key] = SimpleNamespace(
                pk=assessment.pk,
                learner=assessment.learner,
                enrolment=assessment.enrolment,
                term=assessment.term,
                comments=assessment.comments,
                created_at=assessment.created_at,
                updated_at=assessment.updated_at,
                subjects=[],
            )
        grouped[key].subjects.append({
            "subject": assessment.subject,
            "score": assessment.score,
            "maximum_score": assessment.maximum_score,
            "percentage": assessment.percentage,
            "grade": assessment.grade,
        })
    return list(grouped.values())


@login_required
def assessment_list(request):
    queryset = Assessment.objects.select_related("learner", "enrolment", "term").order_by(
        "learner__last_name", "learner__first_name", "term__start_date", "subject"
    )
    return render(request, "learners/assessment_list.html", {"assessments": _assessment_groups(queryset)})


@login_required
def assessment_detail(request, pk):
    assessment = get_object_or_404(Assessment.objects.select_related("learner", "enrolment", "term"), pk=pk)
    queryset = Assessment.objects.filter(
        learner_id=assessment.learner_id,
        enrolment_id=assessment.enrolment_id,
        term_id=assessment.term_id,
    ).select_related("learner", "enrolment", "term").order_by("subject")
    group = _assessment_groups(queryset)[0]
    return render(request, "learners/assessment_detail.html", {"object": assessment, "assessment_group": group})


@login_required
@record_editor_required
def assessment_create(request):
    initial = {"learner": request.GET.get("learner")} if request.GET.get("learner") else None
    form = AssessmentDetailsForm(request.POST or None, initial=initial)
    subject_forms = AssessmentSubjectFormSet(request.POST or None, prefix="subjects")
    if request.method == "POST" and form.is_valid() and subject_forms.is_valid():
        rows = [row for row in subject_forms.cleaned_data if row and row.get("subject")]
        if not rows:
            subject_forms.non_form_errors = lambda: ["Add at least one subject row."]
        else:
            with transaction.atomic():
                for row in rows:
                    Assessment.objects.create(
                        learner=form.cleaned_data["learner"],
                        enrolment=form.cleaned_data["enrolment"],
                        term=form.cleaned_data["term"],
                        maximum_score=form.cleaned_data["maximum_score"],
                        comments=form.cleaned_data["comments"],
                        subject=row["subject"],
                        score=row["score"],
                        grade=row["grade"],
                    )
            messages.success(request, f"{len(rows)} assessment subject(s) recorded successfully.")
            return redirect("learners:assessment_list")
    return render(request, "learners/assessment_form.html", {
        "form": form,
        "subject_forms": subject_forms,
        "creating": True,
        "model_name": "assessment",
    })


@login_required
@record_editor_required
def assessment_update(request, pk):
    assessment = get_object_or_404(Assessment.objects.select_related("learner", "enrolment", "term"), pk=pk)
    group_queryset = Assessment.objects.filter(
        learner_id=assessment.learner_id,
        enrolment_id=assessment.enrolment_id,
        term_id=assessment.term_id,
    ).order_by("subject")
    initial_subjects = [
        {"subject": item.subject, "score": item.score, "grade": item.grade}
        for item in group_queryset
    ]
    form = AssessmentDetailsForm(request.POST or None, instance=assessment)
    subject_forms = AssessmentSubjectFormSet(request.POST or None, initial=initial_subjects, prefix="subjects")
    if request.method == "POST" and form.is_valid() and subject_forms.is_valid():
        rows = [row for row in subject_forms.cleaned_data if row and row.get("subject")]
        if not rows:
            subject_forms.non_form_errors = lambda: ["Add at least one subject row."]
        else:
            with transaction.atomic():
                group_queryset.delete()
                for row in rows:
                    Assessment.objects.create(
                        learner=form.cleaned_data["learner"],
                        enrolment=form.cleaned_data["enrolment"],
                        term=form.cleaned_data["term"],
                        maximum_score=form.cleaned_data["maximum_score"],
                        comments=form.cleaned_data["comments"],
                        subject=row["subject"],
                        score=row["score"],
                        grade=row["grade"],
                    )
            messages.success(request, f"{len(rows)} assessment subject(s) updated successfully.")
            return redirect("learners:assessment_list")
    return render(request, "learners/assessment_form.html", {
        "form": form,
        "subject_forms": subject_forms,
        "creating": False,
        "model_name": "assessment",
        "object": assessment,
    })


@login_required
@record_editor_required
def uneb_result_create(request):
    initial = {"learner": request.GET.get("learner")} if request.GET.get("learner") else None
    form = UNEBResultForm(request.POST or None, initial=initial)
    subject_forms = UNEBSubjectFormSet(request.POST or None, prefix="subjects")
    if request.method == "POST" and form.is_valid() and subject_forms.is_valid():
        rows = [row for row in subject_forms.cleaned_data if row and row.get("subject")]
        if not rows:
            subject_forms.non_form_errors = lambda: ["Add at least one subject performance row."]
        else:
            result = form.save(commit=False)
            result.subjects = {row["subject"].strip(): row["performance"].strip() for row in rows}
            result.recorded_by = request.user
            result.save()
            messages.success(request, "UNEB result recorded successfully.")
            return redirect("learners:uneb_result_list")
    return render(request, "learners/uneb_result_form.html", {
        "form": form,
        "subject_forms": subject_forms,
        "creating": True,
        "model_name": "UNEB result",
    })


@login_required
@record_editor_required
def uneb_result_update(request, pk):
    result = get_object_or_404(UNEBResult, pk=pk)
    initial_subjects = [{"subject": subject, "performance": performance} for subject, performance in (result.subjects or {}).items()]
    form = UNEBResultForm(request.POST or None, instance=result)
    subject_forms = UNEBSubjectFormSet(request.POST or None, initial=initial_subjects, prefix="subjects")
    if request.method == "POST" and form.is_valid() and subject_forms.is_valid():
        rows = [row for row in subject_forms.cleaned_data if row and row.get("subject")]
        if not rows:
            subject_forms.non_form_errors = lambda: ["Add at least one subject performance row."]
        else:
            result = form.save(commit=False)
            result.subjects = {row["subject"].strip(): row["performance"].strip() for row in rows}
            result.save()
            messages.success(request, "UNEB result updated successfully.")
            return redirect("learners:uneb_result_list")
    return render(request, "learners/uneb_result_form.html", {
        "form": form,
        "subject_forms": subject_forms,
        "creating": False,
        "model_name": "UNEB result",
        "object": result,
    })

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
