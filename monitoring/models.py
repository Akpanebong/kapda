from django.conf import settings
from django.db import models
from core.models import TimeStampedModel, School, Location, Term
from projects.models import Project, Indicator


class FieldVisit(TimeStampedModel):
    project = models.ForeignKey(Project,on_delete=models.PROTECT)
    school = models.ForeignKey(School,null=True,blank=True,on_delete=models.SET_NULL)
    visit_date = models.DateField()
    visit_type = models.CharField(max_length=100,blank=True)
    findings = models.TextField()
    recommendations = models.TextField(blank=True)
    conducted_by = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    follow_up_due = models.DateField(null=True,blank=True)

    def __str__(self):
        return f"{self.school} {self.visit_date}"


class FollowUpAction(TimeStampedModel):
    visit = models.ForeignKey(FieldVisit,null=True,blank=True,on_delete=models.CASCADE,related_name="actions")
    activity = models.ForeignKey(Indicator,null=True,blank=True,on_delete=models.CASCADE,related_name="follow_up_actions")
    action = models.TextField()
    responsible_person = models.CharField(max_length=160,blank=True)
    due_date = models.DateField(null=True,blank=True)
    status = models.CharField(max_length=20,choices=[("open","Open"),("in_progress","In progress"),("completed","Completed"),("overdue","Overdue")],default="open")
    completed_date = models.DateField(null=True,blank=True)
    evidence = models.FileField(upload_to="followup_evidence/",blank=True,null=True)

    def __str__(self):
        return f"{self.activity} {self.responsible_person}"

class MHMSession(TimeStampedModel):
    project = models.ForeignKey(Project,on_delete=models.PROTECT)
    school = models.ForeignKey(School,on_delete=models.PROTECT)
    session_date = models.DateField()
    topic = models.CharField(max_length=200)
    facilitator = models.CharField(max_length=160,blank=True)
    girls_attending = models.PositiveIntegerField(default=0)
    boys_attending = models.PositiveIntegerField(default=0)
    other_participants = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.school} {self.session_date}"

class WASHFacility(TimeStampedModel):
    school = models.ForeignKey(School,on_delete=models.PROTECT,related_name="wash_facilities")
    project = models.ForeignKey(Project,on_delete=models.PROTECT)
    facility_type = models.CharField(max_length=100,choices=[("changing_space","Girls' changing/private space"),("handwashing","Handwashing facility"),("water","Water source"),("latrine","Sanitation/latrine"),("other","Other")])
    status = models.CharField(max_length=20,choices=[("functional","Functional"),("needs_repair","Needs repair"),("not_functional","Not functional"),("planned","Planned")],default="functional")
    verified_date = models.DateField()
    findings = models.TextField(blank=True)
    follow_up_action = models.TextField(blank=True)

    def __str__(self):
        return f"{self.school} {self.facility_type}"
