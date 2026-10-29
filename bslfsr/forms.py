from django import forms

from .models import PeaceActivity


class PeaceActivityForm(forms.ModelForm):
    message_channel = forms.ChoiceField(
        choices=[("", "Select channel"), ("radio", "Radio"), ("community_meeting", "Community meeting"), ("school", "School"), ("religious", "Religious institution"), ("social_media", "Social media"), ("other", "Other")],
        required=False,
    )
    class Meta:
        model = PeaceActivity
        fields = [
            "project", "title", "activity_type", "activity_type_other", "message_channel", "message_channel_other", "activity_date",
            "location", "female_participants", "male_participants", "youth_participants", "notes",
        ]
        widgets = {
            "activity_date": forms.DateInput(attrs={"type": "date", "class": "datepicker"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "project": forms.Select(attrs={"class": "form-control"}),
            "location": forms.Select(attrs={"class": "form-control"}),
            "activity_type": forms.Select(attrs={"class": "form-control"}),
            "activity_type_other": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "message_channel": forms.Select(attrs={"class": "form-control"}),
            "message_channel_other": forms.TextInput(attrs={"class": "form-control"}),
            "female_participants": forms.NumberInput(attrs={"class": "form-control"}),
            "male_participants": forms.NumberInput(attrs={"class": "form-control"}),
            "youth_participants": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["activity_type_other"].required = False
        self.fields["message_channel_other"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("activity_type") == "other" and not cleaned.get("activity_type_other", "").strip():
            self.add_error("activity_type_other", "Specify the peacebuilding activity type.")
        if cleaned.get("activity_type") != "other":
            cleaned["activity_type_other"] = ""
        if cleaned.get("activity_type") == "messaging" and not cleaned.get("message_channel"):
            self.add_error("message_channel", "Select the peace message channel.")
        if cleaned.get("message_channel") == "other" and not cleaned.get("message_channel_other", "").strip():
            self.add_error("message_channel_other", "Specify the peace message channel.")
        if cleaned.get("message_channel") != "other":
            cleaned["message_channel_other"] = ""
        if cleaned.get("activity_type") != "messaging":
            cleaned["message_channel"] = ""
            cleaned["message_channel_other"] = ""
        return cleaned
