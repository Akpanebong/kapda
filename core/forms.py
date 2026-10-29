from django import forms

from .models import FieldAttendance, FieldAttendanceParticipant


class FieldAttendanceForm(forms.ModelForm):
    class Meta:
        model = FieldAttendance
        fields = [
            "district", "sub_county", "parish", "village",
            "activity_date", "activity",

        ] # "approved_by", "approved_title", "approved_signature", "county",
        # "approved_date", "submitted_date", submitted_title", "submitted_signature",
        widgets = {
            "activity_date": forms.DateInput(attrs={"type": "date", 'class': 'form-control'}),
            "submitted_date": forms.DateInput(attrs={"type": "date", 'class': 'form-control'}),
            "approved_date": forms.DateInput(attrs={"type": "date", 'class': 'form-control'}),
            "district": forms.TextInput(attrs={'class': 'form-control'}),
            "county": forms.TextInput(attrs={'class': 'form-control'}),
            "sub_county": forms.TextInput(attrs={'class': 'form-control'}),
            "parish": forms.TextInput(attrs={'class': 'form-control'}),
            "village": forms.TextInput(attrs={'class': 'form-control'}),
            "activity": forms.Select(attrs={'class': 'form-control'}),
            "submitted_title": forms.TextInput(attrs={'class': 'form-control'}),
            "submitted_signature": forms.TextInput(attrs={'class': 'form-control'}),
            "approved_title": forms.TextInput(attrs={'class': 'form-control'}),
            "approved_signature": forms.TextInput(attrs={'class': 'form-control'}),
            "approved_by": forms.TextInput(attrs={'class': 'form-control'}),
        }


class FieldAttendanceParticipantForm(forms.ModelForm):
    class Meta:
        model = FieldAttendanceParticipant
        fields = ["name", "sex", "title_role", "contact", "signature"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Participant name"}),
            "sex": forms.Select(attrs={"class": "form-select"}),
            "title_role": forms.TextInput(attrs={"class": "form-control", "placeholder": "Title or role"}),
            "contact": forms.TextInput(attrs={"class": "form-control", "placeholder": "Email or telephone"}),
            "signature": forms.TextInput(attrs={"class": "form-control", "placeholder": "Initials", "readonly": True, "data-auto-initials": "true"}),
        }
