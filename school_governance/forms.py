from django import forms

from core.form_helpers import add_date_time_pickers

from .models import (
    GovernanceAction,
    GovernanceMember,
    GovernanceMeeting,
    GovernanceTraining,
    SchoolImprovementPlan,
)


class GovernanceStyledForm(forms.ModelForm):
    """Apply the project's standard Bootstrap widget classes to governance forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_date_time_pickers(self)


class GovernanceMemberForm(GovernanceStyledForm):
    class Meta:
        model = GovernanceMember
        fields = ["school", "body", "full_name", "sex", "position", "phone", "active", "trained_topics"]
        widgets = {"trained_topics": forms.Textarea(attrs={"rows": 2})}


class GovernanceMeetingForm(GovernanceStyledForm):
    class Meta:
        model = GovernanceMeeting
        fields = ["school", "project", "body", "meeting_date", "agenda", "resolutions", "female_attendees", "male_attendees", "minutes_file"]
        widgets = {
            "meeting_date": forms.DateInput(attrs={"type": "date"}),
            "agenda": forms.Textarea(attrs={"rows": 2}),
            "resolutions": forms.Textarea(attrs={"rows": 2}),
        }


class GovernanceTrainingForm(GovernanceStyledForm):
    class Meta:
        model = GovernanceTraining
        fields = ["school", "body", "topic", "training_date", "participants", "facilitator"]
        widgets = {"training_date": forms.DateInput(attrs={"type": "date"})}


class SchoolImprovementPlanForm(GovernanceStyledForm):
    class Meta:
        model = SchoolImprovementPlan
        fields = ["school", "academic_year", "title", "priority_areas", "status", "reviewed_by"]
        widgets = {"priority_areas": forms.Textarea(attrs={"rows": 2})}


class GovernanceActionForm(GovernanceStyledForm):
    class Meta:
        model = GovernanceAction
        fields = ["meeting", "action", "responsible_person", "due_date", "status"]
        widgets = {
            "action": forms.Textarea(attrs={"rows": 2}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
