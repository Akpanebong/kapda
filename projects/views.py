import json

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.forms import modelform_factory
from .forms import MonitoringFormDefinitionForm, activity_data_form
from .models import ActivityData, Indicator, MonitoringForm, Project
from accounts.access import record_editor_required
from core.form_helpers import add_date_time_pickers, model_fields


def _linked_models_json():
    from django.apps import apps
    allowed_apps = {"core", "projects", "learners", "monitoring", "school_governance", "bslfsr"}
    models = sorted(
        {model for model in apps.get_models() if model._meta.app_label in allowed_apps and model is not ActivityData},
        key=lambda model: (model._meta.verbose_name, model._meta.label_lower),
    )
    return json.dumps([
        {"value": model._meta.label_lower, "label": model._meta.verbose_name.title()}
        for model in models
    ])


@login_required
def indicator_detail(request, pk):
    indicator = get_object_or_404(Indicator.objects.select_related("project", "monitoring_form"), pk=pk)
    return render(request, "projects/indicator_detail.html", {
        "indicator": indicator,
        "entries": indicator.data_entries.select_related("entered_by").order_by("-collection_date", "-created_at")[:10],
    })


def _indicator_form(request, instance=None):
    form_class = modelform_factory(Indicator, fields=model_fields(Indicator))
    return add_date_time_pickers(form_class(
        request.POST or None,
        request.FILES or None,
        instance=instance,
    ))


@login_required
def indicator_list(request):
    indicators = Indicator.objects.select_related("project").order_by("name")
    query = request.GET.get("q", "").strip()
    if query:
        indicators = indicators.filter(name__icontains=query) | indicators.filter(code__icontains=query)
    return render(request, "projects/indicator_list.html", {"indicators": indicators, "query": query})


@login_required
@record_editor_required
def indicator_create(request):
    form = _indicator_form(request)
    if request.method == "POST" and form.is_valid():
        indicator = form.save()
        messages.success(request, "Indicator created successfully.")
        return redirect("projects:indicator_detail", pk=indicator.pk)
    return render(request, "projects/indicator_form.html", {"form": form, "indicator": None, "creating": True, "model_name": "indicator"})


@login_required
@record_editor_required
def indicator_update(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    form = _indicator_form(request, instance=indicator)
    if request.method == "POST" and form.is_valid():
        indicator = form.save()
        messages.success(request, "Indicator updated successfully.")
        return redirect("projects:indicator_detail", pk=indicator.pk)
    return render(request, "projects/indicator_form.html", {"form": form, "indicator": indicator, "creating": False, "model_name": "indicator"})


@login_required
@record_editor_required
@require_POST
def indicator_delete(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    indicator.delete()
    messages.success(request, "Indicator deleted successfully.")
    return redirect("projects:indicator_list")


@login_required
@record_editor_required
def monitoring_form_create(request, indicator_id):
    indicator = get_object_or_404(Indicator, pk=indicator_id)
    if hasattr(indicator, "monitoring_form"):
        return redirect("projects:monitoring_form_update", indicator_id=indicator.pk)
    form = MonitoringFormDefinitionForm(request.POST or None, indicator=indicator)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Indicator monitoring fields saved.")
        return redirect("projects:indicator_detail", pk=indicator.pk)
    return render(request, "projects/monitoring_form_form.html", {
        "form": form,
        "indicator": indicator,
        "creating": True,
        "schema_json": json.dumps(form.instance.schema or []),
        "linked_models_json": _linked_models_json(),
    })


@login_required
@record_editor_required
def monitoring_form_update(request, indicator_id):
    indicator = get_object_or_404(Indicator, pk=indicator_id)
    monitoring_form = get_object_or_404(MonitoringForm, indicator=indicator)
    form = MonitoringFormDefinitionForm(request.POST or None, instance=monitoring_form, indicator=indicator)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Indicator monitoring fields updated.")
        return redirect("projects:indicator_detail", pk=indicator.pk)
    return render(request, "projects/monitoring_form_form.html", {
        "form": form,
        "indicator": indicator,
        "creating": False,
        "schema_json": json.dumps(form.instance.schema or []),
        "linked_models_json": _linked_models_json(),
    })


@login_required
@record_editor_required
@require_POST
def monitoring_form_delete(request, indicator_id):
    indicator = get_object_or_404(Indicator, pk=indicator_id)
    MonitoringForm.objects.filter(indicator=indicator).delete()
    messages.success(request, "Indicator-specific monitoring fields removed. The standard ActivityData form is now used.")
    return redirect("projects:indicator_detail", pk=indicator.pk)


@login_required
def project_dashboard(request):
    qs=Project.objects.all()
    if request.user.role not in {"admin","manager","meal","viewer"} and not request.user.is_superuser:
        qs=qs.filter(assigned_users=request.user)
    projects = list(qs.prefetch_related("activities_indicators"))
    return render(request, "projects/project_dashboard.html", {
        "projects": projects,
        "pending_verification_count": ActivityData.objects.filter(
            verification_status="pending", project__in=projects
        ).count(),
    })


@login_required
@record_editor_required
def activity_data_submit(request, pk):
    activity = get_object_or_404(Indicator.objects.select_related("project", "monitoring_form"), pk=pk, active=True)
    if not activity.project_id:
        messages.error(request, "This activity must be assigned to a project before data can be collected.")
        return redirect("monitoring:activity_dashboard")
    form = activity_data_form(activity)(request.POST or None, request.FILES or None, activity=activity)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.entered_by = request.user
        entry.save()
        messages.success(request, f"Data submitted for {activity.name}.")
    elif request.method == "POST":
        messages.error(request, "Please correct the activity data form and submit again.")
    return redirect("monitoring:activity_dashboard")


# Backwards-compatible Python import for integrations using the old function name.
activity_data_create = activity_data_submit
