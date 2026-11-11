import csv
import json
from io import BytesIO
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from openpyxl import Workbook

from .access import vsla_access_required
from accounts.access import record_editor_required
from .forms import VSLAGroupForm, VSLAMemberForm, SavingsTransactionForm, LoanForm, LoanRepaymentForm, VSLA_MeetingForm, MeetingAttendanceForm, SocialFundTransactionForm
from .models import VSLAGroup, VSLAMember, SavingsTransaction, Loan, LoanRepayment, VSLA_Meeting, MeetingAttendance, SocialFundTransaction, LedgerEntry

from decimal import Decimal

from django.db.models import (
    Count,
    Sum,
    Q,
    F,
    Value,
    Case,
    When,
    OuterRef,
    Subquery,
    ExpressionWrapper,
    DecimalField,
)
from django.db.models.functions import Coalesce
from django.shortcuts import render


@vsla_access_required
def dashboard(request):
    """Optimized VSLA dashboard with database-side portfolio calculations."""

    ZERO = Decimal("0.00")
    MONEY = DecimalField(max_digits=18, decimal_places=2)

    zero_value = Value(ZERO, output_field=MONEY)
    hundred_value = Value(Decimal("100"), output_field=MONEY)

    selected_group = request.GET.get("group", "")
    selected_status = request.GET.get("group_status", "")
    groups_qs = VSLAGroup.objects.all()
    if selected_group.isdigit():
        groups_qs = groups_qs.filter(pk=selected_group)
    else:
        selected_group = ""
    if selected_status in dict(VSLAGroup.Status.choices):
        groups_qs = groups_qs.filter(status=selected_status)
    else:
        selected_status = ""
    group_ids = groups_qs.values("pk")

    # ---------------------------------------------------------
    # 1. Groups and members
    # ---------------------------------------------------------
    group_stats = groups_qs.aggregate(
        total_groups=Count("pk"),
        active_groups=Count(
            "pk",
            filter=Q(status=VSLAGroup.Status.ACTIVE),
        ),
    )

    member_stats = VSLAMember.objects.filter(group_id__in=group_ids).aggregate(
        total_members=Count("pk"),
        active_members=Count(
            "pk",
            filter=Q(status=VSLAMember.Status.ACTIVE),
        ),
    )

    # ---------------------------------------------------------
    # 2. Posted savings
    # ---------------------------------------------------------
    posted_savings = SavingsTransaction.objects.filter(
        status=LedgerEntry.Status.POSTED,
        group_id__in=group_ids,
    )

    savings_stats = posted_savings.aggregate(
        total_savings=Sum(
            "amount",
            filter=Q(
                transaction_type=SavingsTransaction.Type.DEPOSIT,
            ),
        ),
        withdrawals=Sum(
            "amount",
            filter=Q(
                transaction_type__in=[
                    SavingsTransaction.Type.WITHDRAWAL,
                    SavingsTransaction.Type.SHARE_OUT,
                ],
            ),
        ),
    )

    total_savings = savings_stats["total_savings"] or ZERO
    withdrawals = savings_stats["withdrawals"] or ZERO
    net_savings = total_savings - withdrawals

    # ---------------------------------------------------------
    # 3. Loan portfolio
    # ---------------------------------------------------------
    # Calculate posted repayments per loan in a correlated
    # subquery, avoiding a query for every loan property.
    repayment_totals = (
        LoanRepayment.objects.filter(
            loan_id=OuterRef("pk"),
            status=LedgerEntry.Status.POSTED,
        )
        .order_by()
        .values("loan_id")
        .annotate(total=Sum("amount"))
        .values("total")[:1]
    )

    loan_portfolio = Loan.objects.filter(group_id__in=group_ids).annotate(
        dashboard_principal=Coalesce(
            "approved_amount",
            "requested_amount",
            output_field=MONEY,
        ),
        dashboard_repaid=Coalesce(
            Subquery(repayment_totals, output_field=MONEY),
            zero_value,
            output_field=MONEY,
        ),
    ).annotate(
        dashboard_total_due=ExpressionWrapper(
            F("dashboard_principal")
            * (
                hundred_value + F("interest_rate")
            )
            / hundred_value,
            output_field=MONEY,
        ),
    ).annotate(
        dashboard_outstanding=Case(
            When(
                dashboard_total_due__gt=F("dashboard_repaid"),
                then=ExpressionWrapper(
                    F("dashboard_total_due") - F("dashboard_repaid"),
                    output_field=MONEY,
                ),
            ),
            default=zero_value,
            output_field=MONEY,
        ),
    )

    loan_stats = loan_portfolio.aggregate(
        loan_disbursed=Sum(
            "approved_amount",
            filter=Q(
                status__in=[
                    Loan.Status.DISBURSED,
                    Loan.Status.CLOSED,
                ],
            ),
        ),
        outstanding=Sum(
            "dashboard_outstanding",
            filter=Q(status=Loan.Status.DISBURSED),
        ),
        pending_loans=Count(
            "pk",
            filter=Q(status=Loan.Status.SUBMITTED),
        ),
    )

    loan_disbursed = loan_stats["loan_disbursed"] or ZERO
    outstanding = loan_stats["outstanding"] or ZERO

    # Actual posted repayments, rather than estimating repayment
    # as disbursed principal minus outstanding principal.
    total_repaid = (
        LoanRepayment.objects.filter(
            status=LedgerEntry.Status.POSTED,
            loan__status__in=[
                Loan.Status.DISBURSED,
                Loan.Status.CLOSED,
            ],
            loan__group_id__in=group_ids,
        ).aggregate(total=Sum("amount"))["total"]
        or ZERO
    )

    # ---------------------------------------------------------
    # 4. Social fund
    # ---------------------------------------------------------
    social_stats = SocialFundTransaction.objects.filter(
        status=LedgerEntry.Status.POSTED,
        group_id__in=group_ids,
    ).aggregate(
        social_in=Sum(
            "amount",
            filter=Q(
                transaction_type=SocialFundTransaction.Type.CONTRIBUTION,
            ),
        ),
        social_out=Sum(
            "amount",
            filter=Q(
                transaction_type=SocialFundTransaction.Type.SUPPORT,
            ),
        ),
    )

    social_in = social_stats["social_in"] or ZERO
    social_out = social_stats["social_out"] or ZERO
    social_fund_balance = social_in - social_out

    # ---------------------------------------------------------
    # 5. Group status chart
    # ---------------------------------------------------------
    status_counts = list(
        groups_qs.values("status")
        .annotate(total=Count("pk"))
        .order_by("status")
    )

    # ---------------------------------------------------------
    # 6. Recent posted savings and recent loan applications
    # ---------------------------------------------------------
    recent_savings = (
        posted_savings.select_related("group", "member")
        .order_by("-transaction_date", "-created_at")[:8]
    )

    recent_loans = (
        loan_portfolio.select_related("group", "member")
        .order_by("-created_at")[:6]
    )

    # ---------------------------------------------------------
    # 7. Chart data
    # ---------------------------------------------------------
    chart_data = {
        "groupLabels": [
            (item["status"] or "unknown")
            .replace("_", " ")
            .title()
            for item in status_counts
        ],
        "groupValues": [
            item["total"] for item in status_counts
        ],
        "savingsLabels": [
            "Deposits",
            "Withdrawals / share-outs",
        ],
        "savingsValues": [
            float(total_savings),
            float(withdrawals),
        ],
        "loanLabels": [
            "Outstanding",
            "Posted repayments",
        ],
        "loanValues": [
            float(outstanding),
            float(total_repaid),
        ],
    }

    # ---------------------------------------------------------
    # 8. Template context — preserve existing variable names
    # ---------------------------------------------------------
    context = {
        "title": "VSLA Intelligence Dashboard",
        "groups": VSLAGroup.objects.order_by("name"),
        "selected_group": selected_group,
        "selected_status": selected_status,
        "filter_query": request.GET.urlencode(),

        "total_groups": group_stats["total_groups"],
        "active_groups": group_stats["active_groups"],

        "total_members": member_stats["total_members"],
        "active_members": member_stats["active_members"],

        "total_savings": total_savings,
        "net_savings": net_savings,

        "loan_disbursed": loan_disbursed,
        "outstanding_loans": outstanding,
        "pending_loans": loan_stats["pending_loans"],

        "social_fund_balance": social_fund_balance,

        "recent_savings": recent_savings,
        "recent_loans": recent_loans,

        "chart_data": chart_data,
    }

    return render(request, "vsla/vsla_dashboard.html", context)


@vsla_access_required
def group_list(request):
    qs = VSLAGroup.objects.annotate(member_total=Count("members")).order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(code__icontains=q) | qs.filter(project__name__icontains=q) | qs.filter(location__district__icontains=q)
    return render(request, "vsla/group_list.html", {"groups": qs, "q": q, "filter_query": request.GET.urlencode(), "title": "VSLA Groups"})


@vsla_access_required
@record_editor_required
def group_create(request):
    form = VSLAGroupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        messages.success(request, "VSLA group registered successfully.")
        return redirect("vsla:group_detail", slug=obj.slug)
    return render(request, "vsla/group_form.html", {"form": form, "title": "Register VSLA Group", "eyebrow": "GROUP MANAGEMENT", "cancel_url": "vsla:groups"})


@vsla_access_required
def group_detail(request, slug):
    group = get_object_or_404(VSLAGroup, slug=slug)
    member_qs = group.members.all()
    savings_qs = group.savings_transactions.select_related("member", "recorded_by").order_by("-transaction_date")
    loan_qs = group.loans.select_related("member").order_by("-created_at")
    meeting_qs = group.meetings.select_related("recorded_by").annotate(
        attendance_total=Count("attendance", distinct=True),
        attendance_present=Count("attendance", filter=Q(attendance__present=True), distinct=True),
    )
    social_fund_qs = group.social_fund_transactions.select_related("member", "recorded_by").order_by("-transaction_date")
    deposits = group.savings_transactions.filter(status=LedgerEntry.Status.POSTED, transaction_type=SavingsTransaction.Type.DEPOSIT).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    withdrawals = group.savings_transactions.filter(status=LedgerEntry.Status.POSTED, transaction_type__in=[SavingsTransaction.Type.WITHDRAWAL, SavingsTransaction.Type.SHARE_OUT]).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    social_in = social_fund_qs.filter(status=LedgerEntry.Status.POSTED, transaction_type=SocialFundTransaction.Type.CONTRIBUTION).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    social_out = social_fund_qs.filter(status=LedgerEntry.Status.POSTED, transaction_type=SocialFundTransaction.Type.SUPPORT).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    return render(request, "vsla/group_detail.html", {
        "group": group,
        "members": member_qs,
        "transactions": savings_qs[:12],
        "loans": loan_qs[:10],
        "meetings": meeting_qs[:8],
        "social_transactions": social_fund_qs[:12],
        "group_savings": deposits - withdrawals,
        "social_fund_balance": social_in - social_out,
        "member_count": member_qs.count(),
        "savings_count": savings_qs.count(),
        "loan_count": loan_qs.count(),
        "meeting_count": meeting_qs.count(),
        "attendance_count": MeetingAttendance.objects.filter(meeting__group=group).count(),
        "social_fund_count": social_fund_qs.count(),
        "title": group.name,
    })


@vsla_access_required
def member_list(request):
    qs = VSLAMember.objects.select_related("group").all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q) | qs.filter(member_no__icontains=q) | qs.filter(phone__icontains=q)
    group_id = request.GET.get("group")
    if group_id:
        qs = qs.filter(group_id=group_id)
    return render(request, "vsla/member_list.html", {"members": qs, "groups": VSLAGroup.objects.order_by("name"), "q": q, "selected_group": group_id, "filter_query": request.GET.urlencode(), "title": "VSLA Members"})


@vsla_access_required
@record_editor_required
def member_create(request):
    # When registration starts from a group detail page, carry that group
    # into the form so the member is attached to the originating group by
    # default.  The group remains editable for the global member-register
    # workflow, while the normal form validation still protects the saved
    # relationship.
    group_id = request.GET.get("group") or request.POST.get("group")
    initial = {"group": group_id} if group_id else None
    form = VSLAMemberForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.registered_by = request.user
        obj.save()
        messages.success(request, f"{obj.full_name} was registered successfully.")
        return redirect("vsla:member_detail", member_no=obj)
    return render(request, "vsla/member_form.html", {"form": form, "title": "Register Member", "eyebrow": "MEMBER REGISTRY", "cancel_url": "vsla:members"})


@vsla_access_required
def member_detail(request, member_no):
    from core.crud_support import identifier_lookup
    member = get_object_or_404(VSLAMember.objects.select_related("group"), **identifier_lookup(member_no))
    savings = member.savings_transactions.order_by("-transaction_date", "-created_at")[:20]
    loans = member.loans.order_by("-created_at")
    total_saved = member.savings_transactions.filter(status=LedgerEntry.Status.POSTED, transaction_type=SavingsTransaction.Type.DEPOSIT).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    total_out = member.savings_transactions.filter(status=LedgerEntry.Status.POSTED, transaction_type__in=[SavingsTransaction.Type.WITHDRAWAL, SavingsTransaction.Type.SHARE_OUT]).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    return render(request, "vsla/member_detail.html", {"member": member, "savings": savings, "loans": loans, "member_balance": total_saved-total_out, "title": member.full_name})


@vsla_access_required
def savings_list(request):
    qs = SavingsTransaction.objects.select_related("group", "member", "recorded_by").all()
    group_id = request.GET.get("group")
    if group_id:
        qs = qs.filter(group_id=group_id)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(member__first_name__icontains=q) | qs.filter(member__last_name__icontains=q) | qs.filter(transaction_ref__icontains=q) | qs.filter(receipt_no__icontains=q)
    return render(request, "vsla/savings_list.html", {"transactions": qs[:250], "groups": VSLAGroup.objects.order_by("name"), "q": q, "selected_group": group_id, "filter_query": request.GET.urlencode(), "title": "Weekly Savings Ledger"})


@vsla_access_required
@record_editor_required
def savings_create(request):
    initial = {}
    member_id = request.GET.get("member")
    group_id = request.GET.get("group")
    if member_id:
        selected_member = VSLAMember.objects.select_related("group").filter(pk=member_id).first()
        if selected_member:
            initial.update(member=selected_member.pk, group=selected_member.group_id)
    elif group_id:
        initial["group"] = group_id
    form = SavingsTransactionForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.recorded_by = request.user
        try:
            obj.full_clean()
            obj.save()
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"Savings transaction {obj.transaction_ref} recorded.")
            return redirect("vsla:savings")
    return render(request, "vsla/savings_form.html", {"form": form, "title": "Record Weekly Savings", "eyebrow": "SAVINGS LEDGER", "cancel_url": "vsla:savings"})


@vsla_access_required
def loan_list(request):
    qs = Loan.objects.select_related("group", "member", "reviewed_by").all()
    group_id = request.GET.get("group")
    if group_id:
        qs = qs.filter(group_id=group_id)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(loan_no__icontains=q) | qs.filter(member__first_name__icontains=q) | qs.filter(member__last_name__icontains=q)
    return render(request, "vsla/loan_list.html", {"loans": qs[:250], "q": q, "selected_status": status, "selected_group": group_id, "groups": VSLAGroup.objects.order_by("name"), "statuses": Loan.Status.choices, "filter_query": request.GET.urlencode(), "title": "Loan Portfolio"})


@vsla_access_required
@record_editor_required
def loan_create(request):
    initial = {}
    member_id = request.GET.get("member")
    group_id = request.GET.get("group")
    if member_id:
        selected_member = VSLAMember.objects.select_related("group").filter(pk=member_id).first()
        if selected_member:
            initial.update(member=selected_member.pk, group=selected_member.group_id)
    elif group_id:
        initial["group"] = group_id
    form = LoanForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.submitted_by = request.user
        obj.save()
        messages.success(request, f"Loan application {obj.loan_no} saved as draft.")
        return redirect("vsla:loan_detail", loan_no=obj)
    return render(request, "vsla/loan_form.html", {"form": form, "title": "New Loan Application", "eyebrow": "CREDIT MANAGEMENT", "cancel_url": "vsla:loans"})


@vsla_access_required
def loan_detail(request, loan_no):
    from core.crud_support import identifier_lookup
    loan = get_object_or_404(Loan.objects.select_related("group", "member"), **identifier_lookup(loan_no))
    repayments = loan.repayments.filter(status=LedgerEntry.Status.POSTED).order_by("-transaction_date")
    return render(request, "vsla/loan_detail.html", {"loan": loan, "repayments": repayments, "repayment_form": LoanRepaymentForm(), "title": loan.loan_no})


@vsla_access_required
@record_editor_required
@require_POST
def loan_submit(request, loan_no):
    from core.crud_support import identifier_lookup
    loan = get_object_or_404(Loan, **identifier_lookup(loan_no))
    if loan.status != Loan.Status.DRAFT:
        messages.error(request, "Only draft loan applications can be submitted.")
    else:
        loan.status = Loan.Status.SUBMITTED
        loan.save(update_fields=["status", "updated_at"])
        messages.success(request, "Loan application submitted for review.")
    return redirect("vsla:loan_detail", loan_no=loan)


@vsla_access_required
@record_editor_required
@require_POST
def loan_decision(request, loan_no):
    from core.crud_support import identifier_lookup
    loan = get_object_or_404(Loan, **identifier_lookup(loan_no))
    decision = request.POST.get("decision")
    comment = request.POST.get("comment", "").strip()
    if decision in {"approve", "reject"} and loan.status != Loan.Status.SUBMITTED:
        messages.error(request, "Only submitted loan applications can be reviewed.")
    elif decision == "approve":
        try:
            amount = Decimal(request.POST.get("approved_amount") or loan.requested_amount)
            if amount <= 0 or amount > loan.requested_amount:
                raise ValueError
        except (ValueError, ArithmeticError):
            messages.error(request, "Enter a valid approved amount not exceeding the requested amount.")
            return redirect("vsla:loan_detail", loan_no=loan)
        loan.approved_amount = amount
        loan.status = Loan.Status.APPROVED
        loan.reviewed_by = request.user
        loan.reviewed_at = timezone.now()
        loan.decision_comment = comment
        loan.save()
        messages.success(request, "Loan approved. Record disbursement when funds are issued.")
    elif decision == "reject":
        loan.status = Loan.Status.REJECTED
        loan.reviewed_by = request.user
        loan.reviewed_at = timezone.now()
        loan.decision_comment = comment
        loan.save()
        messages.success(request, "Loan application rejected.")
    elif decision == "disburse":
        if loan.status != Loan.Status.APPROVED:
            messages.error(request, "Only approved loans can be disbursed.")
        else:
            loan.status = Loan.Status.DISBURSED
            loan.disbursed_by = request.user
            loan.disbursed_at = timezone.now()
            loan.due_date = timezone.localdate() + timedelta(weeks=loan.duration_weeks)
            loan.save()
            messages.success(request, "Loan marked as disbursed.")
    else:
        messages.error(request, "Unknown loan decision.")
    return redirect("vsla:loan_detail", loan_no=loan)


@vsla_access_required
@record_editor_required
@require_POST
def repayment_create(request, loan_no):
    from core.crud_support import identifier_lookup
    loan = get_object_or_404(Loan, **identifier_lookup(loan_no))
    form = LoanRepaymentForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.loan = loan
        obj.recorded_by = request.user
        try:
            obj.full_clean()
            obj.save()
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Loan repayment recorded.")
    else:
        messages.error(request, "Please correct the repayment details.")
    return redirect("vsla:loan_detail", loan_no=loan)


@vsla_access_required
def meeting_list(request):
    meetings = VSLA_Meeting.objects.select_related("group", "recorded_by").all()
    group_id = request.GET.get("group")
    if group_id:
        meetings = meetings.filter(group_id=group_id)
    return render(request, "vsla/meeting_list.html", {"meetings": meetings[:200], "selected_group": group_id, "groups": VSLAGroup.objects.order_by("name"), "filter_query": request.GET.urlencode(), "title": "Group Meetings"})


@vsla_access_required
@record_editor_required
def meeting_create(request, slug=None):
    group_id = request.GET.get("group") or request.POST.get("group")
    if slug and not group_id:
        group_id = get_object_or_404(VSLAGroup, slug=slug).pk
    selected_group = VSLAGroup.objects.filter(pk=group_id).first() if group_id else None
    initial = {"group": selected_group.pk} if selected_group else None
    form = VSLA_MeetingForm(request.POST or None, initial=initial)
    if selected_group and request.method == "GET":
        form.fields["group"].disabled = True
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if selected_group:
            obj.group = selected_group
        obj.recorded_by = request.user
        try:
            obj.full_clean()
            obj.save()
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Meeting recorded.")
            return redirect("vsla:group_detail", slug=obj.group.slug)
    return render(request, "vsla/meeting_form.html", {"form": form, "group": selected_group, "title": "Record Group Meeting", "eyebrow": "MEETING MANAGEMENT", "cancel_url": "vsla:meetings"})


@vsla_access_required
def attendance_list(request):
    attendance = MeetingAttendance.objects.select_related("meeting__group", "meeting", "member").order_by("-meeting__meeting_date", "member__last_name")
    group_id = request.GET.get("group")
    meeting_id = request.GET.get("meeting")
    if group_id:
        attendance = attendance.filter(meeting__group_id=group_id)
    if meeting_id:
        attendance = attendance.filter(meeting_id=meeting_id)
    return render(request, "vsla/attendance_list.html", {"attendance": attendance[:300], "groups": VSLAGroup.objects.order_by("name"), "selected_group": group_id, "filter_query": request.GET.urlencode(), "title": "Meeting Attendance"})


@vsla_access_required
def attendance_group_list(request, slug):
    group = get_object_or_404(VSLAGroup, slug=slug)
    meetings = group.meetings.select_related("recorded_by").annotate(
        attendance_total=Count("attendance", distinct=True),
        attendance_present=Count("attendance", filter=Q(attendance__present=True), distinct=True),
    )
    return render(request, "vsla/group_attendance.html", {"group": group, "meetings": meetings, "title": f"Attendance - {group.name}"})


@vsla_access_required
def attendance_detail(request, slug, meeting_id):
    group = get_object_or_404(VSLAGroup, slug=slug)
    meeting = get_object_or_404(
        VSLA_Meeting.objects.filter(group=group).annotate(
            attendance_present=Count("attendance", filter=Q(attendance__present=True), distinct=True),
        ),
        pk=meeting_id,
    )
    attendance = meeting.attendance.select_related("member").order_by("member__last_name", "member__first_name")
    return render(request, "vsla/attendance_detail.html", {"group": group, "meeting": meeting, "attendance": attendance, "title": f"Attendance - {group.name}"})


@vsla_access_required
@record_editor_required
def attendance_create(request, slug=None):
    group_id = request.GET.get("group") or request.POST.get("group_id")
    meeting_id = request.GET.get("meeting") or request.POST.get("meeting")
    if slug and not group_id:
        group_id = get_object_or_404(VSLAGroup, slug=slug).pk
    selected_group = VSLAGroup.objects.filter(pk=group_id).first() if group_id else None
    if meeting_id and not selected_group:
        selected_meeting = VSLA_Meeting.objects.select_related("group").filter(pk=meeting_id).first()
        selected_group = selected_meeting.group if selected_meeting else None
        group_id = selected_group.pk if selected_group else None
    form = MeetingAttendanceForm(request.POST or None, group_id=group_id)
    if meeting_id and request.method == "GET" and form.fields["meeting"].queryset.filter(pk=meeting_id).exists():
        form.initial["meeting"] = meeting_id
    if request.method == "POST" and form.is_valid():
        meeting = form.cleaned_data["meeting"]
        present_ids = set(form.cleaned_data["members"].values_list("pk", flat=True))
        members = VSLAMember.objects.filter(group=meeting.group, status=VSLAMember.Status.ACTIVE)
        remarks = form.cleaned_data["remarks"]
        with transaction.atomic():
            for member in members:
                record, _ = MeetingAttendance.objects.update_or_create(
                    meeting=meeting,
                    member=member,
                    defaults={"present": member.pk in present_ids, "remarks": remarks},
                )
                record.full_clean()
        messages.success(request, f"Attendance saved for {members.count()} members.")
        return redirect("vsla:group_detail", slug=meeting.group.slug)
    return render(request, "vsla/attendance_form.html", {"form": form, "group": selected_group, "group_id": group_id, "title": "Record Meeting Attendance", "eyebrow": "MEETING ATTENDANCE", "cancel_url": "vsla:attendance"})


@vsla_access_required
def social_fund_list(request):
    txs = SocialFundTransaction.objects.select_related("group", "member", "recorded_by").all()
    group_id = request.GET.get("group")
    if group_id:
        txs = txs.filter(group_id=group_id)
    return render(request, "vsla/social_fund_list.html", {"transactions": txs[:250], "selected_group": group_id, "groups": VSLAGroup.objects.order_by("name"), "filter_query": request.GET.urlencode(), "title": "Social Fund Ledger"})


@vsla_access_required
@record_editor_required
def social_fund_create(request):
    initial = {}
    member_id = request.GET.get("member")
    group_id = request.GET.get("group")
    if member_id:
        selected_member = VSLAMember.objects.select_related("group").filter(pk=member_id).first()
        if selected_member:
            initial.update(member=selected_member.pk, group=selected_member.group_id)
    elif group_id:
        initial["group"] = group_id
    form = SocialFundTransactionForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.recorded_by = request.user
        try:
            obj.full_clean()
            obj.save()
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Social fund transaction recorded.")
            return redirect("vsla:social_fund")
    return render(request, "vsla/social_fund_form.html", {"form": form, "title": "Record Social Fund Transaction", "eyebrow": "SOCIAL PROTECTION", "cancel_url": "vsla:social_fund"})


def _vsla_export_rows(request, resource):
    """Return a filtered, tabular snapshot for a VSLA register export."""
    group_id = request.GET.get("group")
    status = request.GET.get("status")
    group_status = request.GET.get("group_status")
    q = request.GET.get("q", "").strip()

    scoped_groups = VSLAGroup.objects.all()
    if group_id and str(group_id).isdigit():
        scoped_groups = scoped_groups.filter(pk=group_id)
    if group_status in dict(VSLAGroup.Status.choices):
        scoped_groups = scoped_groups.filter(status=group_status)
    scope_group_ids = scoped_groups.values("pk") if group_id or group_status in dict(VSLAGroup.Status.choices) else None

    def apply_group_scope(queryset, field="group_id"):
        if scope_group_ids is not None:
            return queryset.filter(**{f"{field}__in": scope_group_ids})
        return queryset

    if resource == "groups":
        qs = apply_group_scope(VSLAGroup.objects.select_related("project", "location").all(), "pk")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(project__name__icontains=q) | Q(location__district__icontains=q))
        if group_status not in dict(VSLAGroup.Status.choices) and status in dict(VSLAGroup.Status.choices):
            qs = qs.filter(status=status)
        headers = ["Code", "Group", "Project", "Location", "Weekly share value", "Max shares/week", "Loan interest rate", "Status"]
        rows = ([g.code, g.name, str(g.project or ""), str(g.location or ""), g.weekly_share_value, g.max_shares_per_week, g.loan_interest_rate, g.get_status_display()] for g in qs)
    elif resource == "members":
        qs = VSLAMember.objects.select_related("group").all()
        qs = apply_group_scope(qs)
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(member_no__icontains=q) | Q(phone__icontains=q))
        if status in dict(VSLAMember.Status.choices):
            qs = qs.filter(status=status)
        headers = ["Member no.", "Member", "Group", "Gender", "Phone", "Village", "Status"]
        rows = ([m.member_no, m.full_name, m.group.name, m.get_gender_display(), m.phone, m.village, m.get_status_display()] for m in qs)
    elif resource == "savings":
        qs = SavingsTransaction.objects.select_related("group", "member").all()
        qs = apply_group_scope(qs)
        if q:
            qs = qs.filter(Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) | Q(transaction_ref__icontains=q) | Q(receipt_no__icontains=q))
        if status in dict(LedgerEntry.Status.choices):
            qs = qs.filter(status=status)
        headers = ["Reference", "Date", "Week ending", "Group", "Member", "Type", "Amount", "Status"]
        rows = ([t.transaction_ref, t.transaction_date, t.week_ending, t.group.name, t.member.full_name, t.get_transaction_type_display(), t.amount, t.get_status_display()] for t in qs)
    elif resource == "loans":
        qs = Loan.objects.select_related("group", "member").all()
        qs = apply_group_scope(qs)
        if q:
            qs = qs.filter(Q(loan_no__icontains=q) | Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q))
        if status in dict(Loan.Status.choices):
            qs = qs.filter(status=status)
        headers = ["Loan no.", "Group", "Member", "Application date", "Principal", "Interest rate", "Total due", "Outstanding", "Status"]
        rows = ([l.loan_no, l.group.name, l.member.full_name, l.application_date, l.principal, l.interest_rate, l.total_due, l.outstanding_balance, l.get_status_display()] for l in qs)
    elif resource == "meetings":
        qs = VSLA_Meeting.objects.select_related("group").all()
        qs = apply_group_scope(qs)
        if status in dict(VSLA_Meeting.Status.choices):
            qs = qs.filter(status=status)
        headers = ["Date", "Meeting no.", "Group", "Venue", "Status"]
        rows = ([m.meeting_date, m.meeting_number, m.group.name, m.venue, m.get_status_display()] for m in qs)
    elif resource == "attendance":
        qs = MeetingAttendance.objects.select_related("meeting__group", "member").all()
        qs = apply_group_scope(qs, "meeting__group_id")
        meeting_id = request.GET.get("meeting")
        if meeting_id:
            qs = qs.filter(meeting_id=meeting_id)
        headers = ["Meeting date", "Group", "Meeting no.", "Member", "Present", "Remarks"]
        rows = ([a.meeting.meeting_date, a.meeting.group.name, a.meeting.meeting_number, a.member.full_name, "Yes" if a.present else "No", a.remarks] for a in qs)
    elif resource == "social-fund":
        qs = SocialFundTransaction.objects.select_related("group", "member").all()
        qs = apply_group_scope(qs)
        if status in dict(LedgerEntry.Status.choices):
            qs = qs.filter(status=status)
        headers = ["Reference", "Date", "Group", "Member", "Beneficiary", "Type", "Amount", "Status"]
        rows = ([t.transaction_ref, t.transaction_date, t.group.name, t.member.full_name if t.member else "", t.beneficiary_name, t.get_transaction_type_display(), t.amount, t.get_status_display()] for t in qs)
    else:
        return [], []
    return headers, rows


def _format_export_sheet(sheet):
    """Format exported worksheets so dates render instead of showing ####."""
    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, (date, datetime)):
                cell.number_format = "yyyy-mm-dd"

    for column_cells in sheet.columns:
        column_letter = column_cells[0].column_letter
        longest = 0
        for cell in column_cells:
            value = cell.value
            if value is None:
                continue
            if isinstance(value, (date, datetime)):
                display_value = value.strftime("%Y-%m-%d")
            else:
                display_value = str(value)
            longest = max(longest, len(display_value))
        sheet.column_dimensions[column_letter].width = min(max(longest + 2, 12), 40)


@vsla_access_required
def export_csv(request, resource):
    headers, rows = _vsla_export_rows(request, resource)
    if not headers:
        return HttpResponse("Unknown VSLA export.", status=404)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="vsla_{resource}.csv"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


@vsla_access_required
def export_xlsx(request, resource):
    headers, rows = _vsla_export_rows(request, resource)
    if not headers:
        return HttpResponse("Unknown VSLA export.", status=404)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = resource[:31].replace("-", " ").title()
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = cell.font.copy(bold=True)
    for row in rows:
        sheet.append(list(row))
    _format_export_sheet(sheet)
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="vsla_{resource}.xlsx"'
    return response


@vsla_access_required
def export_workbook(request):
    """Export the complete filtered VSLA workspace as one multi-sheet workbook."""
    workbook = Workbook()
    workbook.remove(workbook.active)

    resources = [
        ("Groups", "groups"),
        ("Members", "members"),
        ("Savings Transactions", "savings"),
        ("Loans", "loans"),
        ("Loan Repayments", None),
        ("Meetings", "meetings"),
        ("Attendance", "attendance"),
        ("Social Fund", "social-fund"),
    ]
    for title, resource in resources:
        if resource:
            headers, rows = _vsla_export_rows(request, resource)
        else:
            group_id = request.GET.get("group")
            group_status = request.GET.get("group_status")
            repayments = LoanRepayment.objects.select_related("loan__group", "loan__member").all()
            if group_id and str(group_id).isdigit():
                repayments = repayments.filter(loan__group_id=group_id)
            if group_status in dict(VSLAGroup.Status.choices):
                repayments = repayments.filter(loan__group__status=group_status)
            headers = ["Reference", "Date", "Loan no.", "Group", "Member", "Amount", "Status"]
            rows = ([r.transaction_ref, r.transaction_date, r.loan.loan_no, r.loan.group.name, r.loan.member.full_name, r.amount, r.get_status_display()] for r in repayments)

        sheet = workbook.create_sheet(title[:31])
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = cell.font.copy(bold=True)
        for row in rows:
            sheet.append(list(row))
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        _format_export_sheet(sheet)

    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="vsla_filtered_workspace.xlsx"'
    return response
