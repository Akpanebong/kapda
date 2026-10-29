from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render

from .form_helpers import add_date_time_pickers, model_fields


def model_form(model, form_class=None):
    return form_class or modelform_factory(model, fields=model_fields(model))


def list_records(request, model, template, context_name=None):
    records = model.objects.all().order_by("-pk")
    query = request.GET.get("q", "").strip()
    if query:
        searchable = [
            field.name for field in model._meta.fields
            if field.get_internal_type() in {"CharField", "TextField", "EmailField"}
        ]
        condition = Q()
        for name in searchable:
            condition |= Q(**{f"{name}__icontains": query})
        records = records.filter(condition)
    page = Paginator(records, 25).get_page(request.GET.get("page"))
    columns = [
        {"name": field.name, "label": field.verbose_name.title()}
        for field in model._meta.fields
        if field.name not in {"id", "updated_at"}
    ]
    return render(request, template, {
        context_name or model._meta.model_name + "s": page,
        "records": page,
        "columns": columns,
        "model_name": model._meta.verbose_name_plural.title(),
        "query": query,
    })


def detail_record(request, model, pk, template):
    record = get_object_or_404(model, pk=pk)
    return render(request, template, {"object": record, "record": record, "model": model})


def create_record(request, model, template, list_url, form_class=None, form_kwargs=None):
    form_type = model_form(model, form_class)
    form = add_date_time_pickers(form_type(request.POST or None, request.FILES or None, **(form_kwargs or {})))
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        for field in ("recorded_by", "entered_by", "created_by"):
            if hasattr(obj, f"{field}_id") and not getattr(obj, f"{field}_id"):
                setattr(obj, field, request.user)
        obj.save()
        form.save_m2m()
        messages.success(request, f"{model._meta.verbose_name.title()} created successfully.")
        return redirect(list_url)
    return render(request, template, {"form": form, "creating": True, "model": model, "model_name": model._meta.verbose_name.title()})


def update_record(request, model, pk, template, list_url, form_class=None):
    obj = get_object_or_404(model, pk=pk)
    form_type = model_form(model, form_class)
    form = add_date_time_pickers(form_type(request.POST or None, request.FILES or None, instance=obj))
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{model._meta.verbose_name.title()} updated successfully.")
        return redirect(list_url)
    return render(request, template, {"form": form, "creating": False, "model": model, "model_name": model._meta.verbose_name.title(), "object": obj})


def delete_record(request, model, pk, list_url):
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, f"{model._meta.verbose_name.title()} deleted.")
    return redirect(list_url)
