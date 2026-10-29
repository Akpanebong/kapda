from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from projects.models import Indicator
from projects.forms import activity_data_form
from .models import FieldVisit, FollowUpAction, MHMSession, WASHFacility

@login_required
def dashboard(request):
    Indicator.sync_overdue()
    activities=Indicator.objects.filter(active=True).select_related("project", "monitoring_form").annotate(reached_total=Sum("data_entries__actual_value"))
    if request.user.role not in {"admin","manager","meal","viewer"} and not request.user.is_superuser:
        activities=activities.filter(project__in=request.user.projects.all())
    activity_cards = [{"activity": activity, "form": activity_data_form(activity)(activity=activity)} for activity in activities.order_by("-created_at")[:12]]
    activity_totals = activities.aggregate(
        total_targets=Sum("target"),
        targets_reached=Sum("data_entries__actual_value"),
    )
    return render(request,"monitoring/activity_dashboard.html",{"activity_cards":activity_cards,"activity_total":activities.count(),"total_targets":activity_totals["total_targets"] or 0,"targets_reached":activity_totals["targets_reached"] or 0,"visits":FieldVisit.objects.count(),"open_actions":FollowUpAction.objects.exclude(status="completed").count(),"mhm_sessions":MHMSession.objects.count(),"wash_facilities":WASHFacility.objects.count()})
