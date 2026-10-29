from uuid import uuid4

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from core.models import Household, Location, TimeStampedModel
from projects.models import Project


class Beneficiary(TimeStampedModel):
    class ParticipantCategory(models.TextChoices):
        GIRL = "girl", "Girl"
        BOY = "boy", "Boy"
        WOMAN = "woman", "Woman"
        MAN = "man", "Man"
        OTHER = "other", "Other / not stated"

    class DisplacementStatus(models.TextChoices):
        HOST = "host", "Host community"
        REFUGEE = "refugee", "Refugee"
        IDP = "idp", "Internally displaced person"
        RETURNEE = "returnee", "Returnee"
        ASYLUM_SEEKER = "asylum_seeker", "Asylum seeker"
        OTHER = "other", "Other / not stated"

    beneficiary_id = models.CharField(max_length=40, unique=True, editable=False)
    full_name = models.CharField(max_length=180)
    sex = models.CharField(max_length=1, choices=[("F", "Female"), ("M", "Male"), ("O", "Other / not stated")])
    date_of_birth = models.DateField(null=True, blank=True)
    estimated_age = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(120)])
    participant_category = models.CharField(max_length=20, choices=ParticipantCategory.choices, default=ParticipantCategory.OTHER, db_index=True)
    displacement_status = models.CharField(max_length=20, choices=DisplacementStatus.choices, default=DisplacementStatus.OTHER, db_index=True)
    disability_status = models.BooleanField(default=False)
    disability_type = models.CharField(max_length=120, blank=True)
    vulnerability_category = models.CharField(max_length=120, blank=True)
    household = models.ForeignKey(Household, null=True, blank=True, on_delete=models.SET_NULL, related_name="beneficiaries")
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    phone = models.CharField(max_length=30, blank=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.beneficiary_id:
            self.beneficiary_id = "KAPDA-BEN-PENDING-" + uuid4().hex[:8].upper()
            super().save(*args, **kwargs)
            self.beneficiary_id = f"KAPDA-BEN-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(beneficiary_id=self.beneficiary_id)
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.beneficiary_id} — {self.full_name}"


class FarmerRecord(TimeStampedModel):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name="farmer_records")
    season = models.CharField(max_length=80)
    crop = models.CharField(max_length=120, blank=True)
    inputs_received = models.TextField(blank=True)
    quantity_distributed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    acreage_planted = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    improved_practices = models.TextField(blank=True)
    yield_harvested = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    food_security_status = models.CharField(max_length=100, blank=True)
    extension_visit_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.beneficiary} - {self.season}"


class PeaceActivity(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=80, choices=[("committee", "Peace committee"), ("dialogue", "Community dialogue"), ("messaging", "Peace messaging"), ("other", "Other")])
    activity_type_other = models.CharField(max_length=160, blank=True, help_text="Specify the activity type when Other is selected")
    message_channel = models.CharField(max_length=80, choices=[("radio", "Radio"), ("community_meeting", "Community meeting"), ("school", "School"), ("religious", "Religious institution"), ("social_media", "Social media"), ("other", "Other")], blank=True)
    message_channel_other = models.CharField(max_length=160, blank=True, help_text="Specify the channel when Other is selected")
    activity_date = models.DateField()
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    female_participants = models.PositiveIntegerField(default=0)
    male_participants = models.PositiveIntegerField(default=0)
    youth_participants = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - ({self.project})"


class PeaceCommittee(TimeStampedModel):
    committee_id = models.CharField(max_length=40, unique=True, blank=True, editable=False)
    name = models.CharField(max_length=180)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.committee_id:
            self.committee_id = "KAPDA-PC-PENDING-" + uuid4().hex[:8].upper()
            super().save(*args, **kwargs)
            self.committee_id = f"KAPDA-PC-{self.pk:04d}"
            type(self).objects.filter(pk=self.pk).update(committee_id=self.committee_id)
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.committee_id} {self.name}'


class PeaceCommitteeMember(TimeStampedModel):
    committee = models.ForeignKey(PeaceCommittee, on_delete=models.CASCADE, related_name="members")
    full_name = models.CharField(max_length=180)
    sex = models.CharField(max_length=1, choices=[("F", "Female"), ("M", "Male"), ("O", "Other / not stated")])
    age_group = models.CharField(max_length=60, blank=True)
    position = models.CharField(max_length=120, blank=True)
    parish = models.CharField(max_length=120, blank=True)
    sub_county = models.CharField(max_length=120, blank=True)
    supported_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.committee} {self.full_name}"


class PeaceCommitteeMeeting(TimeStampedModel):
    committee = models.ForeignKey(PeaceCommittee, on_delete=models.CASCADE, related_name="meetings")
    parish = models.CharField(max_length=120)
    sub_county = models.CharField(max_length=120)
    meeting_date = models.DateField()
    female_participants = models.PositiveIntegerField(default=0)
    male_participants = models.PositiveIntegerField(default=0)
    youth_participants = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.committee} - {self.meeting_date}"
