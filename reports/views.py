import csv
import os
import unicodedata
from datetime import date, timedelta
from io import BytesIO
from xml.sax.saxutils import escape
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q, Sum, Subquery
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from learners.models import Learner, Enrolment, ClassMovement, AttendanceRecord, Assessment, UNEBResult, LearnerSupport, LearnerStatusHistory, LearnerEmployment
from bslfsr.models import Beneficiary, FarmerRecord, PeaceCommittee, PeaceActivity, PeaceCommitteeMember, PeaceCommitteeMeeting
from vsla_app.vsla.models import VSLAGroup, VSLAMember, SavingsTransaction, Loan, LoanRepayment, VSLA_Meeting, SocialFundTransaction
from core.models import School, AuditEvent, AcademicYear, Term, Location
from projects.models import (
    Project,
    Indicator,
    ActivityData,
)
from monitoring.models import FieldVisit, MHMSession, WASHFacility, FollowUpAction

from school_governance.models import GovernanceMember, SchoolImprovementPlan, GovernanceAction, GovernanceTraining, \
    GovernanceMeeting


@login_required
def dashboard(request):
    Indicator.sync_overdue()
    params = {key: request.GET.get(key, "").strip() for key in (
        "project", "phase", "year", "quarter", "month", "term", "school",
        "class", "sex", "age_group", "disability", "parish", "sub_county",
        "participant_category", "status",
    )}

    selected_year = AcademicYear.objects.filter(pk=params["year"]).first() if params["year"].isdigit() else None
    selected_term = Term.objects.filter(pk=params["term"]).first() if params["term"].isdigit() else None

    # Learner filters use fields and relationships that are present in the active schema.
    learners = Learner.objects.all()
    if params["project"]:
        learners = learners.filter(project_links__project_id=params["project"], project_links__active=True)
    if params["school"]:
        learners = learners.filter(enrolments__school_id=params["school"], enrolments__is_current=True)
    if params["class"]:
        learners = learners.filter(current_class=params["class"])
    if params["status"] in dict(Learner.Status.choices):
        learners = learners.filter(status=params["status"])
    if params["sex"] in dict(Learner.Sex.choices):
        learners = learners.filter(sex=params["sex"])
    if params["disability"] in {"yes", "no"}:
        learners = learners.filter(disability_status=params["disability"] == "yes")
    if params["participant_category"] in dict(Learner.ParticipantCategory.choices):
        learners = learners.filter(participant_category=params["participant_category"])
    if params["parish"]:
        learners = learners.filter(location__parish__iexact=params["parish"])
    if params["sub_county"]:
        learners = learners.filter(location__sub_county__iexact=params["sub_county"])
    if selected_year:
        learners = learners.filter(enrolments__academic_year=selected_year)
    elif selected_term:
        learners = learners.filter(enrolments__academic_year=selected_term.academic_year)
    if params["age_group"]:
        learners = _filter_age_group(learners, params["age_group"])
    learners = learners.distinct()
    active_learners = learners.filter(status=Learner.Status.ACTIVE)
    learner_ids = learners.values("pk")
    enrolments = Enrolment.objects.filter(learner_id__in=learner_ids)

    attendance_records = AttendanceRecord.objects.filter(learner_id__in=learner_ids)
    assessment_records = Assessment.objects.filter(learner_id__in=learner_ids)
    uneb_records = UNEBResult.objects.filter(learner_id__in=learner_ids)
    support_records = LearnerSupport.objects.filter(learner_id__in=learner_ids)
    if selected_year:
        attendance_records = attendance_records.filter(term__academic_year=selected_year)
        assessment_records = assessment_records.filter(term__academic_year=selected_year)
        support_records = support_records.filter(term__academic_year=selected_year)
    if selected_term:
        attendance_records = attendance_records.filter(term=selected_term)
        assessment_records = assessment_records.filter(term=selected_term)
        support_records = support_records.filter(term=selected_term)

    # ActivityData owns the reporting dimensions removed from Indicator.
    activity_filters = {}
    if params["project"]: activity_filters["project_id"] = params["project"]
    if params["phase"] in dict(ActivityData.Phase.choices): activity_filters["phase"] = params["phase"]
    if params["school"]: activity_filters["school_id"] = params["school"]
    if params["class"]: activity_filters["class_level"] = params["class"]
    if params["sex"]: activity_filters["sex"] = params["sex"]
    if params["participant_category"]: activity_filters["participant_category"] = params["participant_category"]
    if params["parish"]: activity_filters["parish__iexact"] = params["parish"]
    if params["sub_county"]: activity_filters["sub_county__iexact"] = params["sub_county"]
    if selected_term: activity_filters["term_or_period"] = selected_term
    activity_entries = ActivityData.objects.filter(activity__active=True, **activity_filters)
    if selected_year:
        activity_entries = activity_entries.filter(collection_date__range=(selected_year.start_date, selected_year.end_date))
    if params["quarter"] in {"1", "2", "3", "4"}:
        quarter = int(params["quarter"])
        activity_entries = activity_entries.filter(collection_date__month__in=range((quarter - 1) * 3 + 1, quarter * 3 + 1))
    if params["month"].isdigit() and 1 <= int(params["month"]) <= 12:
        activity_entries = activity_entries.filter(collection_date__month=int(params["month"]))
    activity_scope_selected = bool(activity_filters or selected_year or params["quarter"] or params["month"])
    activities = Indicator.objects.filter(active=True)
    if activity_scope_selected:
        activities = activities.filter(pk__in=Subquery(activity_entries.values("activity_id")))
    activities = activities.annotate(
        reached_total=Sum("data_entries__actual_value", filter=Q(data_entries__in=activity_entries))
    )

    projects = Project.objects.filter(active=True).order_by("name")
    schools = School.objects.filter(active=True).order_by("name")
    years = AcademicYear.objects.order_by("-start_date")
    terms = Term.objects.select_related("academic_year").order_by("-academic_year__start_date", "start_date")
    phases = ActivityData.Phase.choices
    class_choices = Learner._meta.get_field("current_class").choices
    sex_choices = Learner.Sex.choices
    age_groups = [("0-5", "0–5 years"), ("6-9", "6–9 years"), ("10-12", "10–12 years"), ("13-17", "13–17 years"), ("18+", "18 years and above")]
    parishes = Location.objects.exclude(parish="").values_list("parish", flat=True).distinct().order_by("parish")
    sub_counties = Location.objects.exclude(sub_county="").values_list("sub_county", flat=True).distinct().order_by("sub_county")

    activity_status_data = list(activities.values("status").annotate(total=Count("pk")).order_by("status"))
    activity_type_data = list(activities.values("activity_type").annotate(total=Count("pk")).order_by("activity_type"))
    activity_count = activities.count()
    # Delivery KPIs reflect the indicator workflow status. Reach/attainment is
    # a separate measure and must not turn a planned indicator into "completed"
    # merely because its reported value reached the target.
    activity_completed = activities.filter(status=Indicator.Status.COMPLETED).count()
    activity_in_progress = activities.filter(status=Indicator.Status.IN_PROGRESS).count()
    activity_planned = activities.filter(status=Indicator.Status.PLANNED).count()
    activity_delayed = activities.filter(status=Indicator.Status.OVERDUE).count()
    target_reach = activities.aggregate(total=Sum("target"))["total"] or 0
    actual_reach = activity_entries.aggregate(total=Sum("actual_value"))["total"] or 0
    activity_reach = {"target": target_reach, "actual": actual_reach}
    reach_percentage = round(float(actual_reach / target_reach * 100), 1) if target_reach else 0
    filtered_entries = activity_entries
    reach_by = lambda **kwargs: filtered_entries.filter(**kwargs).aggregate(total=Sum("actual_value"))["total"] or 0
    # Sex is a controlled ActivityData field and is the source for the sex-based
    # participant reach totals. Participant category remains available for the
    # girl/boy programme disaggregation.
    activity_reach.update({"women": reach_by(sex="F"), "men": reach_by(sex="M"), "girls": reach_by(participant_category="girl"), "boys": reach_by(participant_category="boy"), "pwd": 0})

    beneficiaries = Beneficiary.objects.all()
    if params["project"]: beneficiaries = beneficiaries.filter(project_id=params["project"])
    if params["sex"] in {"F", "M", "O"}: beneficiaries = beneficiaries.filter(sex=params["sex"])
    if params["disability"] in {"yes", "no"}: beneficiaries = beneficiaries.filter(disability_status=params["disability"] == "yes")
    if params["participant_category"] in dict(Beneficiary.ParticipantCategory.choices): beneficiaries = beneficiaries.filter(participant_category=params["participant_category"])
    if params["parish"]: beneficiaries = beneficiaries.filter(location__parish__iexact=params["parish"])
    if params["sub_county"]: beneficiaries = beneficiaries.filter(location__sub_county__iexact=params["sub_county"])
    if params["age_group"]: beneficiaries = _filter_age_group(beneficiaries, params["age_group"])
    livelihood_summary = {"beneficiaries": beneficiaries.count(), "farmers": FarmerRecord.objects.filter(beneficiary__in=beneficiaries).count(), "vsla_groups": VSLAGroup.objects.count(), "active_vsla_groups": VSLAGroup.objects.filter(status=VSLAGroup.Status.ACTIVE).count(), "vsla_members": VSLAMember.objects.count(), "active_vsla_members": VSLAMember.objects.filter(status=VSLAMember.Status.ACTIVE).count(), "savings_transactions": SavingsTransaction.objects.count(), "loans": Loan.objects.count(), "loan_repayments": LoanRepayment.objects.count(), "social_fund_transactions": SocialFundTransaction.objects.count()}
    governance_summary = {"members": GovernanceMember.objects.count(), "smc_members": GovernanceMember.objects.filter(body=GovernanceMember.Body.SMC).count(), "pta_members": GovernanceMember.objects.filter(body=GovernanceMember.Body.PTA).count(), "meetings": GovernanceMeeting.objects.count(), "smc_meetings": GovernanceMeeting.objects.filter(body=GovernanceMember.Body.SMC).count(), "pta_meetings": GovernanceMeeting.objects.filter(body=GovernanceMember.Body.PTA).count(), "trainings": GovernanceTraining.objects.count(), "improvement_plans": SchoolImprovementPlan.objects.count(), "actions": GovernanceAction.objects.count()}
    service_summary = {"field_visits": FieldVisit.objects.count(), "follow_up_actions": FollowUpAction.objects.count(), "mhm_sessions": MHMSession.objects.count(), "wash_facilities": WASHFacility.objects.count(), "peace_activities": PeaceActivity.objects.count(), "peace_committees": PeaceCommittee.objects.count()}
    total_learners = learners.count()
    assessment_average = assessment_records.aggregate(value=Avg("score"))["value"] or 0
    indicators = Indicator.objects.filter(active=True)
    if params["project"]:
        indicators = indicators.filter(project_id=params["project"])
    age_group_order = [("0-5", "0–5 years"), ("6-9", "6–9 years"), ("10-12", "10–12 years"), ("13-17", "13–17 years"), ("18+", "18 years and above"), ("unknown", "Unknown")]
    age_totals = {key: 0 for key, _ in age_group_order}
    for learner in learners.only("date_of_birth", "estimated_age"):
        age = learner.age
        if age is None:
            key = "unknown"
        elif age <= 5:
            key = "0-5"
        elif age <= 9:
            key = "6-9"
        elif age <= 12:
            key = "10-12"
        elif age <= 17:
            key = "13-17"
        else:
            key = "18+"
        age_totals[key] += 1
    age_data = [{"age_group": label, "total": age_totals[key]} for key, label in age_group_order]
    # Keep scholarship charts independent from the general learner queryset.
    # Completed learners with employment outcomes are never current scholars.
    scholarship_total = Learner.objects.filter(
        status=Learner.Status.ACTIVE,
        on_scholarship=True,
    ).count()
    scholarship_data = [{"status": "Under scholarship", "total": scholarship_total}, {"status": "Not under scholarship", "total": max(total_learners - scholarship_total, 0)}]
    # This chart must never inherit a completed-status filter from the dashboard.
    # It is explicitly scoped to active scholarship learners only.
    active_scholarship = Learner.objects.filter(status=Learner.Status.ACTIVE, on_scholarship=True)
    if params["project"]:
        active_scholarship = active_scholarship.filter(project_links__project_id=params["project"], project_links__active=True)
    if params["school"]:
        active_scholarship = active_scholarship.filter(enrolments__school_id=params["school"], enrolments__is_current=True)
    if params["class"]:
        active_scholarship = active_scholarship.filter(current_class=params["class"])
    if params["sex"] in dict(Learner.Sex.choices):
        active_scholarship = active_scholarship.filter(sex=params["sex"])
    if params["disability"] in {"yes", "no"}:
        active_scholarship = active_scholarship.filter(disability_status=params["disability"] == "yes")
    if params["participant_category"] in dict(Learner.ParticipantCategory.choices):
        active_scholarship = active_scholarship.filter(participant_category=params["participant_category"])
    if params["parish"]:
        active_scholarship = active_scholarship.filter(location__parish__iexact=params["parish"])
    if params["sub_county"]:
        active_scholarship = active_scholarship.filter(location__sub_county__iexact=params["sub_county"])
    if selected_year:
        active_scholarship = active_scholarship.filter(enrolments__academic_year=selected_year)
    elif selected_term:
        active_scholarship = active_scholarship.filter(enrolments__academic_year=selected_term.academic_year)
    if params["age_group"]:
        active_scholarship = _filter_age_group(active_scholarship, params["age_group"])
    scholarship_school_data = list(
        active_scholarship.filter(enrolments__is_current=True)
        .values("enrolments__school__name")
        .annotate(total=Count("pk", distinct=True))
        .order_by("-total", "enrolments__school__name")
    )
    employment_year_data = list(
        LearnerEmployment.objects.filter(learner_id__in=learner_ids, learner__status=Learner.Status.COMPLETED)
        .values("year_employed")
        .annotate(total=Count("learner_id", distinct=True))
        .order_by("year_employed")
    )
    context = {
        "projects": projects, "schools": schools, "years": years, "terms": terms, "phases": phases,
        "class_choices": class_choices, "sex_choices": sex_choices, "age_groups": age_groups,
        "months": [(1, "January"), (2, "February"), (3, "March"), (4, "April"), (5, "May"), (6, "June"), (7, "July"), (8, "August"), (9, "September"), (10, "October"), (11, "November"), (12, "December")],
        "participant_categories": Learner.ParticipantCategory.choices, "statuses": Learner.Status.choices, "parishes": parishes, "sub_counties": sub_counties,
        "project_filter": params["project"], "school_filter": params["school"], "filters": params, "filter_query": request.GET.urlencode(),

        # Education KPIs
        "total": total_learners, "active": active_learners.count(), "girls": learners.filter(sex="F").count(), "boys": learners.filter(sex="M").count(), "other_sex": learners.exclude(sex__in=["F", "M"]).count(), "pwd": learners.filter(disability_status=True).count(), "dropouts": learners.filter(status="dropout").count(), "completed": learners.filter(status="completed").count(), "completion": enrolments.filter(outcome="completed").count(), "transition": ClassMovement.objects.filter(learner_id__in=learner_ids, movement_type="transition").count(), "retention": enrolments.filter(outcome="retained").count(),
        "attendance_count": attendance_records.count(), "assessment_count": assessment_records.count(), "assessment_avg": round(float(assessment_average), 2), "uneb_count": uneb_records.count(), "support_count": support_records.count(), "sanitary_pad_support_count": support_records.filter(support_type="sanitary_pads_mhm").count(), "enrolment_count": enrolments.count(),

        # Activity and participant reach
        "activity_count": activity_count,
        "activity_completed": activity_completed,
        "activity_in_progress": activity_in_progress,
        "activity_planned": activity_planned,
        "activity_delayed": activity_delayed,
        "target_reach": target_reach,
        "actual_reach": actual_reach,
        "reach_percentage": reach_percentage,
        "reach_women": activity_reach["women"] or 0,
        "reach_men": activity_reach["men"] or 0,
        "reach_girls": activity_reach["girls"] or 0,
        "reach_boys": activity_reach["boys"] or 0,
        "reach_pwd": activity_reach["pwd"] or 0,

        # Projects and reporting
        "project_count": Project.objects.count(),
        "active_project_count": projects.count(),
        "indicator_count": indicators.count(),

        # Other programme modules
        "livelihood_summary": livelihood_summary,
        "governance_summary": governance_summary,
        "service_summary": service_summary,

        # Chart and table datasets
        "class_data": list(active_learners.values("current_class").annotate(total=Count("pk")).order_by("current_class")),
        "sex_data": list(learners.values("sex").annotate(total=Count("pk")).order_by("sex")),
        "status_data": list(learners.values("status").annotate(total=Count("pk")).order_by("status")),
        "location_data": list(learners.values("location__district").annotate(total=Count("pk")).order_by("-total")[:8]),
        "age_data": age_data,
        "scholarship_data": scholarship_data,
        "scholarship_school_data": scholarship_school_data,
        "employment_year_data": employment_year_data,
        "activity_status_data": activity_status_data,
        "activity_type_data": activity_type_data,

        # Recent records
        "recent": learners.order_by("-created_at")[:8], "activities": activities.select_related("project").order_by("-created_at")[:6], "audit_events": AuditEvent.objects.order_by("-pk")[:8],
    }

    return render(request, "reports/dashboard.html", context)


def _filter_age_group(queryset, age_group):
    """Filter DOB and estimated-age records consistently with Learner.age_group."""
    today = date.today()
    bounds = {"0-5": (0, 5), "6-9": (6, 9), "10-12": (10, 12), "13-17": (13, 17), "18+": (18, None)}
    minimum, maximum = bounds.get(age_group, (None, None))
    if minimum is None:
        return queryset
    estimated = Q(estimated_age__gte=minimum)
    dob = today.replace(year=today.year - minimum)
    if maximum is None:
        estimated &= Q(estimated_age__isnull=False)
        dob_q = Q(date_of_birth__lte=dob)
    else:
        estimated &= Q(estimated_age__lte=maximum)
        dob_q = Q(date_of_birth__gte=today.replace(year=today.year - maximum - 1) + timedelta(days=1), date_of_birth__lte=dob)
    return queryset.filter((estimated | dob_q)).distinct()


@login_required
def exports(request):
    projects = Project.objects.filter(active=True).order_by("name")
    schools = School.objects.filter(active=True).order_by("name")
    years = AcademicYear.objects.order_by("-start_date")
    terms = Term.objects.select_related("academic_year").order_by("-academic_year__start_date", "start_date")
    return render(request, "reports/exports.html", {
        "projects": projects,
        "schools": schools,
        "years": years,
        "terms": terms,
        "class_choices": Learner._meta.get_field("current_class").choices,
        "sex_choices": Learner.Sex.choices,
        "age_groups": [("0-5", "0-5 years"), ("6-9", "6-9 years"), ("10-12", "10-12 years"), ("13-17", "13-17 years"), ("18+", "18 years and above")],
        "participant_categories": Learner.ParticipantCategory.choices,
        "statuses": Learner.Status.choices,
        "parishes": Location.objects.exclude(parish="").values_list("parish", flat=True).distinct().order_by("parish"),
        "sub_counties": Location.objects.exclude(sub_county="").values_list("sub_county", flat=True).distinct().order_by("sub_county"),
        "filters": request.GET,
        "filter_query": request.GET.urlencode(),
    })


@login_required
def learner_export(request):
    if not (request.user.is_superuser or request.user.role in {"admin","manager","meal","data_entry"}):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to export learner data.")
    qs = _filtered_learner_queryset(request)
    response=HttpResponse(content_type="text/csv")
    response["Content-Disposition"]='attachment; filename="kapda_learners_export.csv"'
    writer=csv.writer(response)
    writer.writerow(["KAPDA ID","First name","Middle name","Last name","Sex","Participant category","Population/displacement status","Age","Age group","Current class","Admission class","Status","Disability","Disability type","District","Sub-county","Parish"])
    for x in qs.distinct().iterator():
        loc=x.location
        writer.writerow([x.reg_no,x.first_name,x.middle_name,x.last_name,x.sex,x.get_participant_category_display(),x.get_displacement_status_display(),x.age,x.age_group,x.current_class,x.class_of_admission,x.status,"Yes" if x.disability_status else "No",x.disability_type,loc.district if loc else "",loc.sub_county if loc else "",loc.parish if loc else ""])
    return response


def _staff_export_allowed(user):
    return user.is_superuser or user.is_staff


def _learner_rows(request):
    qs = _filtered_learner_queryset(request)
    return [["KAPDA ID", "Name", "Sex", "Participant category", "Population status", "Age", "Class", "Status", "District", "Sub-county", "Parish"]] + [
        [x.reg_no, x.full_name, x.get_sex_display(), x.get_participant_category_display(), x.get_displacement_status_display(), x.age or "", x.current_class or "", x.get_status_display(), x.location.district if x.location else "", x.location.sub_county if x.location else "", x.location.parish if x.location else ""]
        for x in qs.distinct().iterator()
    ]


def _filtered_learner_queryset(request):
    qs = Learner.objects.select_related("location").all()
    q = request.GET.get("q", "").strip()
    project = request.GET.get("project", "")
    class_level = request.GET.get("class", "")
    status = request.GET.get("status", "")
    participant_category = request.GET.get("participant_category", "")
    displacement_status = request.GET.get("displacement_status", "")
    school = request.GET.get("school", "")
    sex = request.GET.get("sex", "")
    disability = request.GET.get("disability", "")
    parish = request.GET.get("parish", "")
    sub_county = request.GET.get("sub_county", "")
    age_group = request.GET.get("age_group", "")
    year = request.GET.get("year", "")
    term = request.GET.get("term", "")
    if q:
        qs = qs.filter(Q(reg_no__icontains=q) | Q(first_name__icontains=q) | Q(middle_name__icontains=q) | Q(last_name__icontains=q) | Q(guardian_phone__icontains=q))
    if project:
        qs = qs.filter(project_links__project_id=project, project_links__active=True)
    if school:
        qs = qs.filter(enrolments__school_id=school, enrolments__is_current=True)
    if class_level:
        qs = qs.filter(current_class=class_level)
    if status:
        qs = qs.filter(status=status)
    if participant_category:
        qs = qs.filter(participant_category=participant_category)
    if displacement_status:
        qs = qs.filter(displacement_status=displacement_status)
    if sex in dict(Learner.Sex.choices):
        qs = qs.filter(sex=sex)
    if disability in {"yes", "no"}:
        qs = qs.filter(disability_status=disability == "yes")
    if parish:
        qs = qs.filter(location__parish__iexact=parish)
    if sub_county:
        qs = qs.filter(location__sub_county__iexact=sub_county)
    if age_group:
        qs = _filter_age_group(qs, age_group)
    if year.isdigit():
        qs = qs.filter(enrolments__academic_year_id=year)
    if term.isdigit():
        qs = qs.filter(enrolments__term_id=term)
    return qs.distinct()


def _filtered_beneficiary_queryset(request):
    qs = Beneficiary.objects.select_related("location", "project", "household").all()
    params = request.GET
    if params.get("project"):
        qs = qs.filter(project_id=params["project"])
    if params.get("sex") in {"F", "M", "O"}:
        qs = qs.filter(sex=params["sex"])
    if params.get("disability") in {"yes", "no"}:
        qs = qs.filter(disability_status=params["disability"] == "yes")
    if params.get("participant_category") in dict(Beneficiary.ParticipantCategory.choices):
        qs = qs.filter(participant_category=params["participant_category"])
    if params.get("parish"):
        qs = qs.filter(location__parish__iexact=params["parish"])
    if params.get("sub_county"):
        qs = qs.filter(location__sub_county__iexact=params["sub_county"])
    if params.get("age_group"):
        qs = _filter_age_group(qs, params["age_group"])
    return qs


def _beneficiary_rows(request):
    qs = _filtered_beneficiary_queryset(request)
    return [["Beneficiary ID", "Name", "Sex", "Participant category", "Population status", "Age", "Project", "Household", "District", "Sub-county", "Parish"]] + [
        [x.beneficiary_id, x.full_name, x.get_sex_display(), x.get_participant_category_display(), x.get_displacement_status_display(), x.date_of_birth or x.estimated_age or "", x.project.code, x.household.household_id if x.household else "", x.location.district if x.location else "", x.location.sub_county if x.location else "", x.location.parish if x.location else ""]
        for x in qs.iterator()
    ]


def _xlsx_response(filename, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "KAPDA Report"
    for row in rows:
        sheet.append(row)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2C5D83")
    sheet.freeze_panes = "A2"
    for column in sheet.columns:
        width = min(max(len(str(cell.value or "")) for cell in column) + 2, 32)
        sheet.column_dimensions[column[0].column_letter].width = width
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _pdf_response(filename, title, rows):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5D83")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E3EA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    doc.build(story)
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def learner_export_xlsx(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export learner data.")
    learners = _filtered_learner_queryset(request)
    learner_ids = list(learners.values_list("pk", flat=True))
    workbook = Workbook()
    workbook.remove(workbook.active)

    def add_sheet(title, headers, rows):
        sheet = workbook.create_sheet(title=title[:31])
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2C5D83")
        sheet.freeze_panes = "A2"
        for column in sheet.columns:
            width = min(max(len(str(cell.value or "")) for cell in column) + 2, 36)
            sheet.column_dimensions[column[0].column_letter].width = width

    add_sheet("Learners", ["KAPDA ID", "Name", "Sex", "Participant category", "Population status", "Age", "Admission date", "Admission class", "Current class", "Status", "Disability", "Disability type", "District", "Sub-county", "Parish", "Village"], [
        [x.reg_no, x.full_name, x.get_sex_display(), x.get_participant_category_display(), x.get_displacement_status_display(), x.age or "", x.admission_date, x.class_of_admission, x.current_class, x.get_status_display(), "Yes" if x.disability_status else "No", x.disability_type, x.location.district if x.location else "", x.location.sub_county if x.location else "", x.location.parish if x.location else "", x.location.village if x.location else ""]
        for x in learners.iterator()
    ])
    add_sheet("Education history", ["KAPDA ID", "Learner", "Academic year", "School", "Project", "Class", "Outcome", "Current"], [
        [x.learner.reg_no, x.learner.full_name, x.academic_year.name, x.school.name, x.project.name, x.class_level, x.get_outcome_display(), "Yes" if x.is_current else "No"]
        for x in Enrolment.objects.filter(learner_id__in=learner_ids).select_related("learner", "academic_year", "school", "project").order_by("learner__last_name", "-academic_year__start_date")
    ])
    add_sheet("Support history", ["KAPDA ID", "Learner", "Project", "Support type", "Other support type", "Quantity", "Unit", "Distribution date", "Term", "Notes"], [
        [x.learner.reg_no, x.learner.full_name, x.project.name, x.get_support_type_display(), x.support_type_other, x.quantity, x.unit, x.distribution_date, x.term.name if x.term else "", x.notes]
        for x in LearnerSupport.objects.filter(learner_id__in=learner_ids).select_related("learner", "project", "term").order_by("learner__last_name", "-distribution_date")
    ])
    add_sheet("Attendance", ["KAPDA ID", "Learner", "Academic year", "Term", "School", "Days open", "Days present", "Days absent", "Attendance rate %", "Follow-up required", "Follow-up notes"], [
        [x.learner.reg_no, x.learner.full_name, x.enrolment.academic_year.name, x.term.name, x.enrolment.school.name, x.days_open, x.days_present, x.days_absent, x.attendance_rate, "Yes" if x.follow_up_required else "No", x.follow_up_notes]
        for x in AttendanceRecord.objects.filter(learner_id__in=learner_ids).select_related("learner", "enrolment__academic_year", "enrolment__school", "term").order_by("learner__last_name", "-term__start_date")
    ])
    add_sheet("Assessments", ["KAPDA ID", "Learner", "Academic year", "Term", "Subject", "Score", "Maximum score", "Percentage", "Grade", "Comments"], [
        [x.learner.reg_no, x.learner.full_name, x.enrolment.academic_year.name, x.term.name, x.subject, x.score, x.maximum_score, x.percentage, x.grade, x.comments]
        for x in Assessment.objects.filter(learner_id__in=learner_ids).select_related("learner", "enrolment__academic_year", "term").order_by("learner__last_name", "term__start_date")
    ])
    add_sheet("Status history", ["KAPDA ID", "Learner", "Previous status", "New status", "Effective date", "Reason", "Follow-up action"], [
        [x.learner.reg_no, x.learner.full_name, x.get_previous_status_display(), x.get_new_status_display(), x.effective_date, x.reason, x.follow_up_action]
        for x in LearnerStatusHistory.objects.filter(learner_id__in=learner_ids).select_related("learner").order_by("learner__last_name", "-effective_date")
    ])
    add_sheet("UNEB results", ["KAPDA ID", "Learner", "Examination year", "School", "Academic year", "Level", "Candidate number", "Grade / division", "Aggregate / points", "Remarks"], [
        [x.learner.reg_no, x.learner.full_name, x.examination_year, x.school.name, x.academic_year.name, x.level, x.candidate_number, x.division_grade, x.aggregate_or_points, x.remarks]
        for x in UNEBResult.objects.filter(learner_id__in=learner_ids).select_related("learner", "school", "academic_year").order_by("learner__last_name", "-examination_year")
    ])
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="kapda_learners_comprehensive.xlsx"'
    return response


@login_required
def learner_export_pdf(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export learner data.")
    return _pdf_response("kapda_learners.pdf", "KAPDA Learner Register", _learner_rows(request))


@login_required
def beneficiary_export_xlsx(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export beneficiary data.")
    return _xlsx_response("kapda_beneficiaries.xlsx", _beneficiary_rows(request))


@login_required
def beneficiary_export_pdf(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export beneficiary data.")
    return _pdf_response("kapda_beneficiaries.pdf", "KAPDA Beneficiary Register", _beneficiary_rows(request))


def _peacebuilding_summary_rows(request):
    project_id = request.GET.get("project", "")
    activities = PeaceActivity.objects.select_related("project", "location").all()
    committees = PeaceCommittee.objects.all()
    if project_id:
        activities = activities.filter(project_id=project_id)
        committees = committees.filter(project_id=project_id)
    committee_ids = committees.values_list("pk", flat=True)
    members = PeaceCommitteeMember.objects.filter(committee_id__in=committee_ids, active=True)
    meetings = PeaceCommitteeMeeting.objects.filter(committee_id__in=committee_ids)
    dialogues = activities.filter(activity_type="dialogue")
    messages = activities.filter(activity_type="messaging")
    return [
        ["Indicator", "Value", "Definition"],
        ["Peace committee members supported", members.count(), "Active supported committee members"],
        ["Peace committee meetings", meetings.count(), "Periodic committee meetings recorded"],
        ["Community dialogues", dialogues.count(), "Dialogue activities recorded"],
        ["Dialogue participants", sum((x.female_participants or 0) + (x.male_participants or 0) for x in dialogues), "Female plus male dialogue participants"],
        ["Peace messages disseminated", messages.count(), "Peace messaging activities recorded"],
        ["Community members reached", sum((x.female_participants or 0) + (x.male_participants or 0) for x in activities), "Female plus male participants/reach recorded"],
        ["Women participating", sum(x.female_participants or 0 for x in activities), "Female participants recorded across peace activities"],
        ["Youth participating", sum(x.youth_participants or 0 for x in activities) + sum(x.youth_participants or 0 for x in meetings), "Youth participants recorded across activities and meetings"],
    ]


@login_required
def peacebuilding_export_xlsx(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export peacebuilding data.")
    return _xlsx_response("kapda_peacebuilding_report.xlsx", _peacebuilding_summary_rows(request))


@login_required
def peacebuilding_export_pdf(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export peacebuilding data.")
    return _pdf_response("kapda_peacebuilding_report.pdf", "KAPDA Peacebuilding Report", _peacebuilding_summary_rows(request))


def _programme_export_datasets(request=None):
    """Return the complete livelihoods, food-security and peacebuilding registers."""
    datasets = [
        ("Beneficiaries", _filtered_beneficiary_queryset(request) if request else Beneficiary.objects.all()),
        ("Food security", FarmerRecord.objects.select_related("beneficiary", "beneficiary__project")),
        ("VSLA groups", VSLAGroup.objects.select_related("project", "location")),
        ("VSLA members", VSLAMember.objects.select_related("group")),
        ("Savings transactions", SavingsTransaction.objects.select_related("group", "member")),
        ("Loans", Loan.objects.select_related("group", "member")),
        ("Loan repayments", LoanRepayment.objects.select_related("loan", "loan__group", "loan__member")),
        ("VSLA meetings", VSLA_Meeting.objects.select_related("group")),
        ("Social fund", SocialFundTransaction.objects.select_related("group", "member")),
        ("Peace activities", PeaceActivity.objects.select_related("project", "location")),
        ("Peace committees", PeaceCommittee.objects.select_related("project", "location")),
        ("Committee members", PeaceCommitteeMember.objects.select_related("committee")),
        ("Committee meetings", PeaceCommitteeMeeting.objects.select_related("committee")),
    ]
    if request and request.GET.get("project"):
        project_id = request.GET["project"]
        related_filters = {
            "Food security": {"beneficiary__project_id": project_id},
            "VSLA groups": {"project_id": project_id},
            "VSLA members": {"group__project_id": project_id},
            "Savings transactions": {"group__project_id": project_id},
            "Loans": {"group__project_id": project_id},
            "Loan repayments": {"loan__group__project_id": project_id},
            "VSLA meetings": {"group__project_id": project_id},
            "Social fund": {"group__project_id": project_id},
            "Peace activities": {"project_id": project_id},
            "Peace committees": {"project_id": project_id},
            "Committee members": {"committee__project_id": project_id},
            "Committee meetings": {"committee__project_id": project_id},
        }
        datasets = [(title, queryset.filter(**related_filters[title]) if title in related_filters else queryset) for title, queryset in datasets]
    return datasets


def _dataset_rows(model, queryset):
    fields = [field for field in model._meta.fields if field.name not in {"id", "created_at", "updated_at"}]
    headers = [field.verbose_name.title() for field in fields]
    rows = []
    for record in queryset.iterator():
        row = []
        for field in fields:
            value = getattr(record, field.name)
            if field.is_relation:
                value = str(value) if value is not None else ""
            else:
                display_method = getattr(record, f"get_{field.name}_display", None)
                value = display_method() if display_method else value
            if hasattr(value, "tzinfo") and value.tzinfo is not None:
                value = value.replace(tzinfo=None)
            row.append(value if value is not None else "")
        rows.append(row)
    return headers, rows


def _comprehensive_programme_export_xlsx(filename, request=None):
    workbook = Workbook()
    workbook.remove(workbook.active)
    for title, queryset in _programme_export_datasets(request):
        model = queryset.model
        headers, rows = _dataset_rows(model, queryset)
        sheet = workbook.create_sheet(title=title[:31])
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2C5D83")
        sheet.freeze_panes = "A2"
        for column in sheet.columns:
            width = min(max(len(str(cell.value or "")) for cell in column) + 2, 36)
            sheet.column_dimensions[column[0].column_letter].width = width
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _comprehensive_programme_export_pdf(filename, request=None):
    regular_font, bold_font = _pdf_unicode_fonts()
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=18, rightMargin=18, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    styles["Title"].fontName = bold_font
    styles["Heading2"].fontName = bold_font
    story = [Paragraph("KAPDA Livelihoods, Food Security &amp; Peacebuilding Report", styles["Title"]), Spacer(1, 10)]
    available_width = landscape(A4)[0] - doc.leftMargin - doc.rightMargin
    for title, queryset in _programme_export_datasets(request):
        headers, rows = _dataset_rows(queryset.model, queryset)
        table_style = getSampleStyleSheet()["BodyText"].clone("export_table")
        table_style.fontName = regular_font
        table_style.fontSize = 4.8
        table_style.leading = 5.6
        header_style = getSampleStyleSheet()["BodyText"].clone("export_header")
        header_style.fontName = bold_font
        header_style.fontSize = 5
        header_style.leading = 5.8
        table_data = [[Paragraph(escape(_pdf_safe_text(value)), header_style) for value in headers]]
        table_data.extend([
            [Paragraph(escape(_pdf_safe_text(value)), table_style) for value in row]
            for row in rows
        ])
        column_width = available_width / max(len(headers), 1)
        story.append(Paragraph(escape(title), styles["Heading2"]))
        story.append(Table(table_data, colWidths=[column_width] * len(headers), repeatRows=1, hAlign="CENTER", style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5D83")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E3EA")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F8")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])))
        story.append(Spacer(1, 8))
    doc.build(story)
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _pdf_safe_text(value):
    """Keep generated PDFs readable across fonts and PDF text extractors."""
    text = str(value or "")
    for source, replacement in {
        "â€”": "-", "â€“": "-", "â€‘": "-", "â€¦": "...",
        "—": "-", "–": "-", "‑": "-", "’": "'", "‘": "'",
        "“": '"', "”": '"', "Â": "",
    }.items():
        text = text.replace(source, replacement)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _pdf_unicode_fonts():
    """Register a Unicode-capable font when the host provides one."""
    regular_name, bold_name = "KAPDAArial", "KAPDAArialBold"
    regular_path = r"C:\Windows\Fonts\arial.ttf"
    bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    if os.path.exists(regular_path) and os.path.exists(bold_path):
        if regular_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(regular_name, regular_path))
            pdfmetrics.registerFont(TTFont(bold_name, bold_path))
        return regular_name, bold_name
    return "Helvetica", "Helvetica-Bold"


@login_required
def livelihoods_food_security_peacebuilding_export_xlsx(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export programme data.")
    return _comprehensive_programme_export_xlsx("KAPDA_Livelihoods_Food_Security_Peacebuilding_Report.xlsx", request)


@login_required
def livelihoods_food_security_peacebuilding_export_pdf(request):
    if not _staff_export_allowed(request.user):
        return HttpResponseForbidden("You do not have permission to export programme data.")
    return _comprehensive_programme_export_pdf("KAPDA_Livelihoods_Food_Security_Peacebuilding_Report.pdf", request)
