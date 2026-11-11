from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Assessment, AttendanceRecord, Learner, Enrolment, LearnerProject, LearnerSupport, LearnerEmployment, LearnerStatusHistory, UNEBResult
from projects.models import Project


def _add_form_control_classes(form):
    for field in form.fields.values():
        classes = field.widget.attrs.get("class", "").split()
        if "form-control" not in classes:
            classes.append("form-control")
        field.widget.attrs["class"] = " ".join(classes)


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = "__all__"

    def __init__(self, *args, learner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.locked_learner = learner
        if learner is not None:
            self.fields["learner"].initial = learner.pk
            self.fields["learner"].disabled = True
            self.fields["learner"].widget = forms.HiddenInput()
            self.fields["enrolment"].queryset = Enrolment.objects.filter(
                learner=learner
            ).select_related("school", "academic_year")


class LearnerForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset=Project.objects.filter(active=True), required=True, label="Project")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["disability_status"].widget.attrs.update({
            "id": "id_disability_status",
            "data-disability-toggle": "true",
        })
        self.fields["disability_type"].widget.attrs.update({
            "id": "id_disability_type",
        })

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("disability_status"):
            cleaned["disability_type"] = ""
        return cleaned

    class Meta:
        model = Learner
        fields = ["first_name","middle_name","last_name","sex","date_of_birth","estimated_age",
                  "participant_category","displacement_status",
                  "disability_status","disability_type","admission_date","class_of_admission",
                  "current_class","status","on_scholarship","guardian_name","guardian_phone","location", "project", "notes"]
        widgets = {
            "date_of_birth":forms.DateInput(format="%Y-%m-%d", attrs={"type":"date"}),
            "admission_date":forms.DateInput(format="%Y-%m-%d", attrs={"type":"date"}),
            "notes":forms.Textarea(attrs={"rows":2})}


class EnrolmentForm(forms.ModelForm):
    class Meta:
        model = Enrolment
        fields = ["school","project","academic_year","class_level"]


class AssessmentDetailsForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ["learner", "enrolment", "term", "maximum_score", "comments"]
        widgets = {"comments": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control_classes(self)


class AssessmentSubjectForm(forms.Form):
    subject = forms.CharField(max_length=100, label="Subject")
    score = forms.DecimalField(min_value=0, max_digits=6, decimal_places=2, label="Score")
    grade = forms.CharField(max_length=10, required=False, label="Grade")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control_classes(self)


class UNEBResultForm(forms.ModelForm):
    class Meta:
        model = UNEBResult
        exclude = ["subjects", "recorded_by"]
        widgets = {"remarks": forms.Textarea(attrs={"rows": 2})}


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control_classes(self)


class UNEBSubjectForm(forms.Form):
    subject = forms.CharField(max_length=100, label="Subject")
    performance = forms.CharField(max_length=30, label="Performance / grade")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control_classes(self)


class SupportMaterialForm(forms.Form):
    material = forms.ChoiceField(choices=LearnerSupport.SCHOLASTIC_MATERIAL_CHOICES, label="Material")
    quantity = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2, label="Quantity")
    unit = forms.CharField(max_length=40, initial="pieces", label="Unit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control_classes(self)


AssessmentSubjectFormSet = forms.formset_factory(AssessmentSubjectForm, extra=1)
UNEBSubjectFormSet = forms.formset_factory(UNEBSubjectForm, extra=1)
SupportMaterialFormSet = forms.formset_factory(SupportMaterialForm, extra=1)


class LearnerEmploymentForm(forms.ModelForm):
    class Meta:
        model = LearnerEmployment
        fields = ["employer", "job_title", "year_employed", "employment_type", "work_location", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3, 'class': 'form-control'}),
            "employer": forms.TextInput(attrs={'class': 'form-control'}),
            "job_title": forms.TextInput(attrs={'class': 'form-control'}),
            "year_employed": forms.NumberInput(attrs={'class': 'form-control'}),
            "employment_type": forms.Select(attrs={'class': 'form-control'}),
            "work_location": forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, learner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.learner = learner or getattr(self.instance, "learner", None)

    def clean(self):
        cleaned = super().clean()
        if self.learner and self.learner.status != Learner.Status.COMPLETED:
            raise ValidationError("Only learners marked Completed can have an employment outcome recorded.")
        return cleaned


class LearnerStatusHistoryForm(forms.ModelForm):
    class Meta:
        model = LearnerStatusHistory
        fields = ["previous_status", "new_status", "effective_date", "reason", "follow_up_action"]
        widgets = {
            "effective_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", 'class': 'form-control'}),
            "follow_up_action": forms.Textarea(attrs={"rows": 3, 'class': 'form-control'}),
            "reason": forms.Textarea(attrs={"rows": 3, 'class': 'form-control'}),
            "previous_status": forms.Select(attrs={'class': 'form-control'}),
            "new_status": forms.Select(attrs={'class': 'form-control'}),

        }

    def __init__(self, *args, learner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.learner = learner
        if learner:
            self.fields["previous_status"].initial = learner.status
            self.fields["previous_status"].disabled = True
            self.fields["effective_date"].initial = timezone.localdate()


class LearnerSupportForm(forms.ModelForm):
    class Meta:
        model = LearnerSupport
        fields = ["learner", "project", "support_type", "scholastic_material",
                  "support_type_other", "quantity", "unit", "distribution_date", "term", "notes"]
        widgets = {
            "distribution_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        learner = kwargs.pop("learner", None)
        super().__init__(*args, **kwargs)
        _add_form_control_classes(self)
        self.fields["quantity"].required = False
        self.fields["unit"].required = False
        if learner is not None:
            self.fields["learner"].initial = learner.pk
            self.fields["learner"].disabled = True
            self.fields["project"].queryset = Project.objects.filter(active=True)
            active_project = learner.project_links.filter(active=True).order_by("-start_date").first()
            if active_project and not self.initial.get("project"):
                self.fields["project"].initial = active_project.project_id
        if not self.initial.get("distribution_date"):
            self.fields["distribution_date"].initial = timezone.localdate()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("support_type") != "scholastic_materials":
            cleaned["scholastic_material"] = ""
            if not cleaned.get("quantity"):
                self.add_error("quantity", "Enter the quantity of support provided.")
            if not cleaned.get("unit", "").strip():
                self.add_error("unit", "Enter the unit, for example pieces, packages, or sessions.")
        else:
            cleaned["quantity"] = None
            cleaned["unit"] = ""
        if cleaned.get("support_type") == "other" and not cleaned.get("support_type_other", "").strip():
            raise ValidationError({"support_type_other": "Specify the other type of support."})
        if cleaned.get("support_type") != "other":
            cleaned["support_type_other"] = ""
        return cleaned
