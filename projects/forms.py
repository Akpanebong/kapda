from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify

from core.models import School
from learners.models import Learner
from bslfsr.models import Beneficiary
from .models import AGE_RANGE_CHOICES, SUPPORT_TYPE_CHOICES, ActivityData, MonitoringForm


# These are the only fields that every custom activity form receives. Every
# other value must be explicitly added by the form designer and is stored in
# ActivityData.attributes (or as a selected linked record).
COMMON_ACTIVITY_FIELDS = {"collection_date", "reporting_period", "phase", "actual_value"}


def _linked_record_models():
    allowed_apps = {"core", "projects", "learners", "monitoring", "school_governance", "bslfsr"}
    return sorted(
        {model for model in apps.get_models() if model._meta.app_label in allowed_apps and model is not ActivityData},
        key=lambda model: (model._meta.verbose_name, model._meta.label_lower),
    )


class ActivityDataForm(forms.ModelForm):
    age = forms.ChoiceField(choices=[("", "Select age range")] + AGE_RANGE_CHOICES, required=False)
    support_type = forms.ChoiceField(choices=[("", "Select support type")] + SUPPORT_TYPE_CHOICES, required=False)

    class Meta:
        model = ActivityData
        fields = [
            "collection_date", "reporting_period", "phase", "actual_value", "data_source", "evidence",
            "sex", "age", "class_level", "school", "learner", "beneficiary", "parish", "sub_county",
            "support_type", "distribution_date", "term_or_period", "quantity", "material_type",
            "topic", "facilitator", "participant_category", "barrier_category", "facility_type",
            "action_type", "findings", "follow_up_action", "attributes", "comments",
            "verification_status",
        ]
        widgets = {
            "collection_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "distribution_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "findings": forms.Textarea(attrs={"rows": 2}),
            "follow_up_action": forms.Textarea(attrs={"rows": 2}),
            "comments": forms.Textarea(attrs={"rows": 2}),
            "attributes": forms.Textarea(attrs={"rows": 2, "placeholder": '{"custom_field": "value"}'}),
        }

    def __init__(self, *args, activity=None, **kwargs):
        self.activity = activity
        super().__init__(*args, **kwargs)
        self.fields["collection_date"].initial = self.initial.get("collection_date") or timezone.localdate()
        if activity is not None:
            self.fields["school"].queryset = School.objects.filter(active=True).order_by("name")
            self.fields["school"].label = "School / institution"
            self.fields["learner"].queryset = Learner.objects.filter(status__in=[Learner.Status.ACTIVE, Learner.Status.COMPLETED]).order_by("last_name", "first_name")
            self.fields["learner"].label = "Learner"
            self.fields["beneficiary"].queryset = Beneficiary.objects.filter(active=True).order_by("full_name")
            self.fields["beneficiary"].label = "Beneficiary"
            for configured in activity.configured_attributes:
                key = configured.lower().replace("/", "_").replace("-", "_").replace(" ", "_")
                if key in self.fields:
                    self.fields[key].label = configured.replace("_", " ").title()
                    self.fields[key].required = True
                else:
                    self.fields[f"custom_{key}"] = forms.CharField(label=configured, required=True)
            self.fields["attributes"].required = False
            self.fields["actual_value"].label = f"Reached / actual ({activity.unit})"

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.activity = self.activity
        obj.project = self.activity.project
        custom = {}
        for name in list(self.cleaned_data):
            if name.startswith("custom_") and self.cleaned_data.get(name) not in (None, ""):
                custom[name[7:]] = self.cleaned_data[name]
        supplied = self.cleaned_data.get("attributes") or {}
        if isinstance(supplied, str):
            import json
            try:
                supplied = json.loads(supplied)
            except (TypeError, ValueError):
                supplied = {"notes": supplied}
        obj.attributes = {**supplied, **custom}
        if commit:
            obj.save()
        return obj


class MonitoringFormDefinitionForm(forms.ModelForm):
    schema = forms.JSONField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Add sections and fields below. The form structure is saved automatically.",
    )

    class Meta:
        model = MonitoringForm
        fields = ["indicator", "description", "schema", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "indicator": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, indicator=None, **kwargs):
        self.route_indicator = indicator
        super().__init__(*args, **kwargs)
        if indicator is not None:
            self.fields["indicator"].initial = indicator.pk
            self.fields["indicator"].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.route_indicator is not None:
            instance.indicator = self.route_indicator
        if commit:
            instance.save()
        return instance

    def clean_schema(self):
        schema = self.cleaned_data.get("schema") or []
        if not isinstance(schema, list):
            raise ValidationError("Schema must be a JSON array of sections.")
        names = set()
        linked_record_count = 0
        allowed = {"text", "textarea", "email", "integer", "decimal", "date", "boolean", "choice", "foreign_key"}
        foreign_key_targets = {model._meta.label_lower for model in _linked_record_models()}
        for section_index, section in enumerate(schema, 1):
            if not isinstance(section, dict) or not section.get("title") or not isinstance(section.get("fields", []), list):
                raise ValidationError(f"Section {section_index} must have a title and fields array.")
            for field_index, definition in enumerate(section["fields"], 1):
                if not isinstance(definition, dict) or not definition.get("name") or not definition.get("label"):
                    raise ValidationError(f"Section {section_index}, field {field_index} needs name and label.")
                key = slugify(str(definition["name"])).replace("-", "_")
                if not key or key in names or key in COMMON_ACTIVITY_FIELDS:
                    raise ValidationError(f"Field name '{definition.get('name')}' is duplicated or reserved.")
                if definition.get("type", "text") not in allowed:
                    raise ValidationError(f"Unsupported field type for '{definition['name']}'.")
                if definition.get("type") == "choice" and not isinstance(definition.get("choices", []), list):
                    raise ValidationError(f"Choices for '{definition['name']}' must be a list.")
                if definition.get("type") == "foreign_key" and definition.get("target") not in foreign_key_targets:
                    raise ValidationError(f"Linked record field '{definition['name']}' must target one of the available programme models.")
                if definition.get("type") == "foreign_key":
                    linked_record_count += 1
                    if linked_record_count > 1:
                        raise ValidationError("An activity form can contain only one Linked record field. Choose the applicable model for that field.")
                names.add(key)
        return schema


class SchemaActivityDataForm(forms.Form):
    collection_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    actual_value = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    reporting_period = forms.ChoiceField(choices=[("", "Select reporting period")]+list(ActivityData.ReportingPeriod.choices), required=False, widget=forms.Select(attrs={"class": "form-select"}))
    phase = forms.ChoiceField(choices=[("", "Select phase")]+list(ActivityData.Phase.choices), required=False, widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, activity=None, **kwargs):
        self.activity = activity
        self.foreign_key_fields = {}
        self.generic_link_fields = {}
        super().__init__(*args, **kwargs)
        self.fields["collection_date"].initial = self.initial.get("collection_date") or timezone.localdate()
        schema = getattr(getattr(activity, "monitoring_form", None), "schema", []) if activity else []
        for section in schema or []:
            for definition in section.get("fields", []):
                key = slugify(str(definition.get("name", ""))).replace("-", "_")
                field_type = definition.get("type", "text")
                options = {"label": definition.get("label", key.replace("_", " ").title()), "required": bool(definition.get("required", False)), "help_text": definition.get("help_text", "")}
                if field_type == "textarea":
                    field = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}), **options)
                elif field_type == "email":
                    field = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}), **options)
                elif field_type == "integer":
                    field = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}), **options)
                elif field_type == "decimal":
                    field = forms.DecimalField(widget=forms.NumberInput(attrs={"class": "form-control"}), **options)
                elif field_type == "date":
                    field = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}), **options)
                elif field_type == "boolean":
                    field = forms.BooleanField(widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), **options)
                elif field_type == "choice":
                    choices = [(item.get("value", item), item.get("label", item)) if isinstance(item, dict) else (item, item) for item in definition.get("choices", [])]
                    field = forms.ChoiceField(choices=[("", "Select")]+choices, widget=forms.Select(attrs={"class": "form-select"}), **options)
                elif field_type == "foreign_key":
                    target = definition.get("target")
                    target_model = apps.get_model(target)
                    if target_model is None:
                        raise ValidationError(f"Unsupported linked record target: {target}")
                    self.generic_link_fields[key] = target_model
                    field = forms.ModelChoiceField(queryset=target_model.objects.all().order_by("pk"), empty_label="Select linked record", **options)
                else:
                    field = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), **options)
                self.fields[key] = field

    def save(self, commit=True):
        values = {key: self.cleaned_data[key] for key in self.fields if key not in COMMON_ACTIVITY_FIELDS and key not in self.generic_link_fields and self.cleaned_data.get(key) not in (None, "")}
        obj = ActivityData(
            activity=self.activity,
            project=self.activity.project,
            collection_date=self.cleaned_data["collection_date"],
            actual_value=self.cleaned_data.get("actual_value") or 0,
            reporting_period=self.cleaned_data.get("reporting_period") or "",
            phase=self.cleaned_data.get("phase") or "",
        )
        for field_name, target in self.foreign_key_fields.items():
            if self.cleaned_data.get(field_name) is not None:
                setattr(obj, target, self.cleaned_data[field_name])
        for field_name, target_model in self.generic_link_fields.items():
            linked = self.cleaned_data.get(field_name)
            if linked is not None:
                obj.linked_record_type = ContentType.objects.get_for_model(target_model)
                obj.linked_record_id = linked.pk
                break
        obj.attributes = values
        if commit:
            obj.save()
        return obj


def activity_data_form(activity):
    monitoring_form = getattr(activity, "monitoring_form", None)
    if monitoring_form and monitoring_form.is_active and monitoring_form.schema:
        return SchemaActivityDataForm
    return ActivityDataForm
