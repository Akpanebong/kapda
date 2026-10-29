from django.db import models
from django.conf import settings
from core.models import TimeStampedModel, School
from projects.models import Project


class GovernanceMember(TimeStampedModel):
    class Body(models.TextChoices): SMC="SMC","School Management Committee / BOG"; PTA="PTA","Parent Teacher Association"
    school=models.ForeignKey(School,on_delete=models.PROTECT,related_name="governance_members")
    body=models.CharField(max_length=10,choices=Body.choices)
    full_name=models.CharField(max_length=180)
    sex=models.CharField(max_length=1,choices=[("F","Female"),("M","Male"),("O","Other / not stated")])
    position=models.CharField(max_length=100)
    phone=models.CharField(max_length=30,blank=True)
    active=models.BooleanField(default=True)
    trained_topics=models.TextField(blank=True)

    def __str__(self):
        return f"{self.full_name} — {self.body}"


class GovernanceMeeting(TimeStampedModel):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    project=models.ForeignKey(Project,null=True,blank=True,on_delete=models.SET_NULL)
    body=models.CharField(max_length=10,choices=GovernanceMember.Body.choices)
    meeting_date=models.DateField()
    agenda=models.TextField(blank=True)
    resolutions=models.TextField(blank=True)
    female_attendees=models.PositiveIntegerField(default=0)
    male_attendees=models.PositiveIntegerField(default=0)
    minutes_file=models.FileField(upload_to="governance/minutes/",blank=True,null=True)

    def __str__(self):
        return f"{self.school} {self.meeting_date}"

class GovernanceTraining(TimeStampedModel):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    body=models.CharField(max_length=10,choices=GovernanceMember.Body.choices)
    topic=models.CharField(max_length=200)
    training_date=models.DateField()
    participants=models.ManyToManyField(GovernanceMember,blank=True)
    facilitator=models.CharField(max_length=160,blank=True)

    def __str__(self):
        return f"{self.school} {self.topic}"


class SchoolImprovementPlan(TimeStampedModel):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    academic_year=models.ForeignKey("core.AcademicYear",on_delete=models.PROTECT)
    title=models.CharField(max_length=220)
    priority_areas=models.TextField()
    status=models.CharField(max_length=20,choices=[("draft","Draft"),("approved","Approved"),("in_progress","In progress"),("completed","Completed")],default="draft")
    reviewed_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.school} {self.academic_year}"

class GovernanceAction(TimeStampedModel):
    meeting=models.ForeignKey(GovernanceMeeting,on_delete=models.CASCADE,related_name="actions")
    action=models.TextField()
    responsible_person=models.CharField(max_length=160,blank=True)
    due_date=models.DateField(null=True,blank=True)
    status=models.CharField(max_length=20,choices=[("open","Open"),("in_progress","In progress"),("completed","Completed")],default="open")

    def __str__(self):
        return f"{self.meeting} {self.action}"