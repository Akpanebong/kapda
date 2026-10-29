from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (GovernanceActionForm, GovernanceMemberForm, GovernanceMeetingForm,
                    GovernanceTrainingForm, SchoolImprovementPlanForm)
from .models import (GovernanceAction, GovernanceMember, GovernanceMeeting,
                     GovernanceTraining, SchoolImprovementPlan)
from accounts.access import record_editor_required


def _list(request, title, description, headings, records, values, create_url, edit_name, delete_name, template):
    rows = [{"values": row_values, "edit_url": reverse(edit_name, kwargs={"pk": record.pk}),
             "delete_url": reverse(delete_name, kwargs={"pk": record.pk})}
            for record, row_values in zip(records, values)]
    return render(request, template, {"title": title, "description": description,
        "headings": headings, "rows": rows, "create_url": create_url})


def _form(request, form_class, title, cancel_url, template, instance=None):
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(cancel_url)
    return render(request, template, {"form": form, "title": title, "cancel_url": cancel_url})


@login_required
def governance_dashboard(request):
    return render(request, "governance/governance_dashboard.html", {
        "members": GovernanceMember.objects.filter(active=True).count(),
        "smc": GovernanceMember.objects.filter(active=True, body="SMC").count(),
        "pta": GovernanceMember.objects.filter(active=True, body="PTA").count(),
        "meetings": GovernanceMeeting.objects.count(), "trainings": GovernanceTraining.objects.count(),
        "plans": SchoolImprovementPlan.objects.count(),
        "open_actions": GovernanceAction.objects.exclude(status="completed").count(),
    })


@login_required
def governance_member_list(request):
    records = GovernanceMember.objects.select_related("school").order_by("full_name")
    return _list(request, "Governance members", "governance members", ["Name", "School", "Body", "Position", "Active"], records,
                 ([r.full_name, r.school, r.get_body_display(), r.position, "Yes" if r.active else "No"] for r in records), reverse("governance:governance_member_create"), "governance:governance_member_update", "governance:governance_member_delete", "governance/governance_member_list.html")

@login_required
@record_editor_required
def governance_member_create(request):
    return _form(request, GovernanceMemberForm, "Add governance member", reverse("governance:governance_member_list"), "governance/governance_member_form.html")

@login_required
@record_editor_required
def governance_member_update(request, pk):
    return _form(request, GovernanceMemberForm, "Edit governance member", reverse("governance:governance_member_list"), "governance/governance_member_form.html", get_object_or_404(GovernanceMember, pk=pk))

@login_required
@record_editor_required
def governance_member_delete(request, pk):
    if request.method == "POST": get_object_or_404(GovernanceMember, pk=pk).delete()
    return redirect("governance:governance_member_list")


@login_required
def governance_meeting_list(request):
    records = GovernanceMeeting.objects.select_related("school", "project").order_by("-meeting_date")
    return _list(request, "Governance meetings", "governance meetings", ["School", "Body", "Date", "Project", "Minutes"], records,
                 ([r.school, r.get_body_display(), r.meeting_date, r.project, "Available" if r.minutes_file else "Not provided"] for r in records), reverse("governance:governance_meeting_create"), "governance:governance_meeting_update", "governance:governance_meeting_delete", "governance/governance_meeting_list.html")

@login_required
@record_editor_required
def governance_meeting_create(request):
    return _form(request, GovernanceMeetingForm, "Add governance meeting", reverse("governance:governance_meeting_list"), "governance/governance_meeting_form.html")

@login_required
@record_editor_required
def governance_meeting_update(request, pk):
    return _form(request, GovernanceMeetingForm, "Edit governance meeting", reverse("governance:governance_meeting_list"), "governance/governance_meeting_form.html", get_object_or_404(GovernanceMeeting, pk=pk))

@login_required
@record_editor_required
def governance_meeting_delete(request, pk):
    if request.method == "POST": get_object_or_404(GovernanceMeeting, pk=pk).delete()
    return redirect("governance:governance_meeting_list")


@login_required
def governance_training_list(request):
    records = GovernanceTraining.objects.select_related("school").order_by("-training_date")
    return _list(request, "Governance training", "governance training records", ["School", "Body", "Topic", "Date", "Facilitator"], records,
                 ([r.school, r.get_body_display(), r.topic, r.training_date, r.facilitator] for r in records), reverse("governance:governance_training_create"), "governance:governance_training_update", "governance:governance_training_delete", "governance/governance_training_list.html")

@login_required
@record_editor_required
def governance_training_create(request):
    return _form(request, GovernanceTrainingForm, "Add governance training", reverse("governance:governance_training_list"), "governance/governance_training_form.html")

@login_required
@record_editor_required
def governance_training_update(request, pk):
    return _form(request, GovernanceTrainingForm, "Edit governance training", reverse("governance:governance_training_list"), "governance/governance_training_form.html", get_object_or_404(GovernanceTraining, pk=pk))

@login_required
@record_editor_required
def governance_training_delete(request, pk):
    if request.method == "POST": get_object_or_404(GovernanceTraining, pk=pk).delete()
    return redirect("governance:governance_training_list")


@login_required
def school_improvement_plan_list(request):
    records = SchoolImprovementPlan.objects.select_related("school", "academic_year").order_by("-academic_year__start_date")
    return _list(request, "School improvement plans", "school improvement plans", ["School", "Title", "Academic year", "Status"], records,
                 ([r.school, r.title, r.academic_year, r.get_status_display()] for r in records), reverse("governance:school_improvement_plan_create"), "governance:school_improvement_plan_update", "governance:school_improvement_plan_delete", "governance/school_improvement_plan_list.html")

@login_required
@record_editor_required
def school_improvement_plan_create(request):
    return _form(request, SchoolImprovementPlanForm, "Add school improvement plan", reverse("governance:school_improvement_plan_list"), "governance/school_improvement_plan_form.html")

@login_required
@record_editor_required
def school_improvement_plan_update(request, pk):
    return _form(request, SchoolImprovementPlanForm, "Edit school improvement plan", reverse("governance:school_improvement_plan_list"), "governance/school_improvement_plan_form.html", get_object_or_404(SchoolImprovementPlan, pk=pk))

@login_required
@record_editor_required
def school_improvement_plan_delete(request, pk):
    if request.method == "POST": get_object_or_404(SchoolImprovementPlan, pk=pk).delete()
    return redirect("governance:school_improvement_plan_list")


@login_required
def governance_action_list(request):
    records = GovernanceAction.objects.select_related("meeting", "meeting__school").order_by("status", "due_date")
    return _list(request, "Governance actions", "governance actions", ["Action", "Meeting", "Responsible", "Due date", "Status"], records,
                 ([r.action, r.meeting, r.responsible_person, r.due_date, r.get_status_display()] for r in records), reverse("governance:governance_action_create"), "governance:governance_action_update", "governance:governance_action_delete", "governance/governance_action_list.html")

@login_required
@record_editor_required
def governance_action_create(request):
    return _form(request, GovernanceActionForm, "Add governance action", reverse("governance:governance_action_list"), "governance/governance_action_form.html")

@login_required
@record_editor_required
def governance_action_update(request, pk):
    return _form(request, GovernanceActionForm, "Edit governance action", reverse("governance:governance_action_list"), "governance/governance_action_form.html", get_object_or_404(GovernanceAction, pk=pk))

@login_required
@record_editor_required
def governance_action_delete(request, pk):
    if request.method == "POST": get_object_or_404(GovernanceAction, pk=pk).delete()
    return redirect("governance:governance_action_list")
