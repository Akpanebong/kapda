from django import forms
from django.utils import timezone
from core.models import Location
from projects.models import Project
from .models import VSLAGroup, VSLAMember, SavingsTransaction, Loan, LoanRepayment, VSLA_Meeting, SocialFundTransaction, MeetingAttendance


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model_field_names = {item.name for item in self._meta.model._meta.fields}
        for name, field in self.fields.items():
            widget = field.widget
            model_field = self._meta.model._meta.get_field(name) if name in model_field_names else None
            internal_type = model_field.get_internal_type() if model_field else ""
            if internal_type == "DateField":
                field.widget = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"})
            elif internal_type == "TimeField":
                field.widget = forms.TimeInput(format="%H:%M", attrs={"type": "time", "class": "form-control"})
            elif internal_type == "DateTimeField":
                field.widget = forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"})
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if isinstance(widget, forms.Textarea):
                widget.attrs["rows"] = 2


class MemberSelect(forms.Select):
    """Select widget carrying each member's group for client-side syncing."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value and hasattr(self, "member_groups"):
            group_id = self.member_groups.get(str(value))
            if group_id:
                option["attrs"]["data-group-id"] = str(group_id)
        return option


class ProjectSelect(forms.Select):
    project_donors = {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        raw_value = getattr(value, "value", value)
        donor = self.project_donors.get(str(raw_value))
        if donor is not None:
            option["attrs"]["data-donor"] = donor or "Donor not specified"
        return option


class VSLAGroupForm(StyledModelForm):
    donor_name = forms.CharField(label="Donor", required=False, disabled=True)

    class Meta:
        model = VSLAGroup
        fields = ["name", "project", "donor_name", "location", "meeting_day", "meeting_location", "weekly_share_value", "max_shares_per_week", "loan_interest_rate", "loan_duration_weeks", "start_date", "cycle_end_date", "status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        projects = Project.objects.filter(active=True).order_by("name")
        self.fields["project"].queryset = projects
        self.fields["project"].required = True
        self.fields["project"].widget = ProjectSelect(attrs={"class": "form-select"})
        self.fields["project"].widget.choices = self.fields["project"].choices
        self.fields["project"].widget.project_donors = {str(project.pk): project.donor for project in projects}
        selected_project = self.data.get("project") or getattr(self.instance, "project_id", None)
        donor = self.fields["project"].widget.project_donors.get(str(selected_project), "")
        self.fields["donor_name"].initial = donor or "Donor not specified"
        self.fields["location"].queryset = Location.objects.order_by("district", "sub_county", "parish", "village")


class VSLAMemberForm(StyledModelForm):
    class Meta:
        model = VSLAMember
        fields = ["group", "first_name", "last_name", "gender", "date_of_birth", "phone", "national_id", "household_id", "village", "disability_inclusion", "refugee_or_host_community", "joined_on", "status", "next_of_kin", "next_of_kin_phone", "consent_for_data", "notes"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}), "joined_on": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 2})}


class SavingsTransactionForm(StyledModelForm):
    member = forms.ModelChoiceField(queryset=VSLAMember.objects.all(), widget=MemberSelect)

    class Meta:
        model = SavingsTransaction
        fields = ["group", "member", "transaction_type", "amount", "transaction_date", "week_ending", "receipt_no", "notes"]
        widgets = {"transaction_date": forms.DateInput(attrs={"type": "date"}),
                   "week_ending": forms.DateInput(attrs={"type": "date"}),
                   "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transaction_date"].initial = timezone.localdate()
        self.fields["week_ending"].initial = timezone.localdate()
        group_id = self.data.get("group") or self.initial.get("group") or getattr(self.instance, "group_id", None)
        if group_id:
            self.fields["member"].queryset = VSLAMember.objects.filter(group_id=group_id).order_by("last_name", "first_name")
        else:
            self.fields["member"].queryset = VSLAMember.objects.select_related("group").order_by("group__name", "last_name", "first_name")
        self.fields["member"].widget.member_groups = {
            str(pk): group_id for pk, group_id in VSLAMember.objects.values_list("pk", "group_id")
        }


class LoanForm(StyledModelForm):
    member = forms.ModelChoiceField(queryset=VSLAMember.objects.all(), widget=MemberSelect)

    class Meta:
        model = Loan
        fields = ["group", "member", "requested_amount", "interest_rate", "duration_weeks", "application_date", "purpose"]
        widgets = {"application_date": forms.DateInput(attrs={"type": "date"}), "purpose": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group_id = self.data.get("group") or self.initial.get("group") or getattr(self.instance, "group_id", None)
        if group_id:
            self.fields["member"].queryset = VSLAMember.objects.filter(group_id=group_id).order_by("last_name", "first_name")
        else:
            self.fields["member"].queryset = VSLAMember.objects.select_related("group").order_by("group__name", "last_name", "first_name")
        self.fields["member"].widget.member_groups = {
            str(pk): member_group_id
            for pk, member_group_id in VSLAMember.objects.values_list("pk", "group_id")
        }


class LoanRepaymentForm(StyledModelForm):
    class Meta:
        model = LoanRepayment
        fields = ["amount", "transaction_date", "receipt_no", "notes"]
        widgets = {"transaction_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 2})}


class VSLA_MeetingForm(StyledModelForm):
    class Meta:
        model = VSLA_Meeting
        fields = ["group", "meeting_date", "meeting_number", "venue", "agenda", "minutes", "status", "recorded_by"]
        widgets = {"meeting_date": forms.DateInput(attrs={"type": "date"}), "agenda": forms.Textarea(attrs={"rows": 2}), "minutes": forms.Textarea(attrs={"rows": 2})}


class SocialFundTransactionForm(StyledModelForm):
    member = forms.ModelChoiceField(queryset=VSLAMember.objects.all(), required=False, widget=MemberSelect)

    class Meta:
        model = SocialFundTransaction
        fields = ["group", "member", "transaction_type", "beneficiary_name", "amount", "transaction_date", "receipt_no", "notes"]
        widgets = {"transaction_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group_id = self.data.get("group") or self.initial.get("group") or getattr(self.instance, "group_id", None)
        if group_id:
            self.fields["member"].queryset = VSLAMember.objects.filter(group_id=group_id).order_by("last_name", "first_name")
        else:
            self.fields["member"].queryset = VSLAMember.objects.select_related("group").order_by("group__name", "last_name", "first_name")
        self.fields["member"].widget.member_groups = {
            str(pk): member_group_id
            for pk, member_group_id in VSLAMember.objects.values_list("pk", "group_id")
        }
