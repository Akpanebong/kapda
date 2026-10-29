from django import forms


def model_fields(model):
    excluded = {"id", "created_at", "updated_at", "reg_no", "beneficiary_id", "school_code", "household_id", "group_id", "member_id", "committee_id", "disaggregate_sex", "disaggregate_age", "disaggregate_disability"}
    return [field.name for field in model._meta.fields if field.editable and field.name not in excluded]


def add_date_time_pickers(form):
    model = form._meta.model
    for name, bound_field in form.fields.items():
        existing_classes = bound_field.widget.attrs.get("class", "").split()
        if isinstance(bound_field.widget, forms.Select):
            widget_class = "form-select"
        elif isinstance(bound_field.widget, forms.CheckboxInput):
            widget_class = "form-check-input"
        else:
            widget_class = "form-control"
        existing_classes = [
            css_class for css_class in existing_classes
            if css_class not in {"form-control", "form-select", "form-check-input"}
        ]
        bound_field.widget.attrs["class"] = " ".join(existing_classes + [widget_class]).strip()
        try:
            model_field = model._meta.get_field(name)
        except Exception:
            continue
        internal_type = model_field.get_internal_type()
        if internal_type == "DateField":
            bound_field.widget = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"})
        elif internal_type == "TimeField":
            bound_field.widget = forms.TimeInput(format="%H:%M", attrs={"type": "time", "class": "form-control"})
        elif internal_type == "DateTimeField":
            bound_field.widget = forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"})
        elif isinstance(bound_field.widget, forms.Textarea):
            bound_field.widget.attrs["rows"] = 2
    return form
