from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel, Term

AGE_RANGE_CHOICES = [("0-5", "0–5 years"), ("6-9", "6–9 years"), ("10-12", "10–12 years"), ("13-17", "13–17 years"), ("18-24", "18–24 years"), ("25+", "25 years and above")]
SUPPORT_TYPE_CHOICES = [("sanitary_pads", "Sanitary pads"), ("reusable_menstrual_pads", "Reusable menstrual pads"), ("scholastic_materials", "Scholastic materials"), ("mentorship", "Mentorship / MHM education"), ("transport", "Transport support"), ("back_to_school", "Back-to-school support"), ("other", "Other")]


class Project(TimeStampedModel):
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)
    donor = models.CharField(max_length=180, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Indicator(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=240)
    project = models.ForeignKey(Project, null=True, on_delete=models.CASCADE, related_name="activities_indicators")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED, db_index=True)
    definition = models.TextField(blank=True)
    activity_type = models.CharField(max_length=120, blank=True, help_text="Programme activity or indicator category")
    unit = models.CharField(max_length=60, default="people")
    frequency = models.CharField(max_length=80, blank=True, help_text="e.g. Each distribution, termly, annual")
    target = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Approved target for this activity/indicator")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    attribute_fields = models.TextField(blank=True, help_text="Comma-separated extra attributes to collect")
    calculation_method = models.CharField(max_length=20, choices=[("count", "Count"), ("sum", "Sum"), ("percentage", "Percentage"), ("average", "Average"), ("manual", "Manual entry")], default="count")
    active = models.BooleanField(default=True)

    @property
    def configured_attributes(self):
        return [item.strip() for item in self.attribute_fields.replace("\n", ",").split(",") if item.strip()]

    @property
    def reached(self):
        return self.data_entries.aggregate(total=models.Sum("actual_value"))["total"] or 0

    @property
    def attainment_percentage(self):
        return round(float(self.reached / self.target * 100), 1) if self.target else 0

    @property
    def is_overdue(self):
        return bool(self.end_date and self.end_date < timezone.localdate() and self.status not in {self.Status.COMPLETED, self.Status.CANCELLED})

    @property
    def effective_status(self):
        return self.Status.OVERDUE if self.is_overdue else self.status

    def get_effective_status_display(self):
        return dict(self.Status.choices).get(self.effective_status, self.effective_status)

    @classmethod
    def sync_overdue(cls):
        return cls.objects.filter(end_date__lt=timezone.localdate()).exclude(status__in=[cls.Status.COMPLETED, cls.Status.CANCELLED]).exclude(status=cls.Status.OVERDUE).update(status=cls.Status.OVERDUE)

    def save(self, *args, **kwargs):
        if self.is_overdue:
            self.status = self.Status.OVERDUE
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.name}"


class MonitoringForm(TimeStampedModel):
    """Optional compact data-capture schema for one activity/indicator."""
    indicator = models.OneToOneField(Indicator, on_delete=models.CASCADE, related_name="monitoring_form")
    description = models.TextField(blank=True)
    schema = models.JSONField(default=list, blank=True, help_text="Ordered sections with field definitions. Leave empty to use the standard ActivityData form.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["indicator__name"]

    def __str__(self):
        return f"Monitoring form: {self.indicator.name}"


class ActivityData(TimeStampedModel):
    class ReportingPeriod(models.TextChoices):
        MONTH = "month", "Month"
        QUARTER = "quarter", "Quarter"
        TERM = "term", "Term"
        SEASON = "season", "Season"
        ANNUAL = "annual", "Annual"

    class Phase(models.TextChoices):
        YEAR_1 = "year_1", "Year 1"
        YEAR_2 = "year_2", "Year 2"
        YEAR_3 = "year_3", "Year 3"
        F_YEAR = "f_year", "financial / programme year"

    class Verification(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        CORRECTION = "correction", "Requires correction"

    class Sex(models.TextChoices):
        FEMALE = "F", "Female"; MALE = "M", "Male"; OTHER = "O", "Other / not stated"

    activity = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name="data_entries")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activity_data")
    collection_date = models.DateField()
    actual_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    reporting_period = models.CharField(max_length=20, choices=ReportingPeriod.choices, blank=True)
    sex = models.CharField(max_length=1, choices=Sex.choices)
    phase = models.CharField(max_length=255, choices=Phase.choices, blank=True)
    age = models.CharField(max_length=40, choices=AGE_RANGE_CHOICES, blank=True)
    # age_group = models.CharField(max_length=60, blank=True)
    class_level = models.CharField(max_length=3, choices=[(f"P{i}", f"P{i}") for i in range(1, 8)] + [(f"S{i}", f"S{i}") for i in range(1, 7)], blank=True)
    school = models.ForeignKey("core.School", null=True, blank=True, on_delete=models.SET_NULL)
    learner = models.ForeignKey("learners.Learner", null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_data")
    beneficiary = models.ForeignKey("bslfsr.Beneficiary", null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_data")
    linked_record_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_data_links")
    linked_record_id = models.PositiveBigIntegerField(null=True, blank=True)
    linked_record = GenericForeignKey("linked_record_type", "linked_record_id")
    parish = models.CharField(max_length=120, blank=True)
    sub_county = models.CharField(max_length=120, blank=True)
    support_type = models.CharField(max_length=160, choices=SUPPORT_TYPE_CHOICES, blank=True)
    distribution_date = models.DateField(null=True, blank=True)
    term_or_period = models.ForeignKey(Term, null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_data")
    quantity = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    material_type = models.CharField(max_length=160, blank=True)
    topic = models.CharField(max_length=240, blank=True)
    facilitator = models.CharField(max_length=160, blank=True)
    participant_category = models.CharField(max_length=120, blank=True)
    barrier_category = models.CharField(max_length=160, blank=True)
    facility_type = models.CharField(max_length=160, blank=True)
    action_type = models.CharField(max_length=160, blank=True)
    findings = models.TextField(blank=True)
    follow_up_action = models.TextField(blank=True)
    attributes = models.JSONField(default=dict, blank=True, help_text="Additional activity-specific disaggregation or attributes")
    data_source = models.CharField(max_length=200, blank=True)
    evidence = models.FileField(upload_to="activity_data_evidence/%Y/%m/", blank=True, null=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="activity_data_entries")
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="verified_activity_data")
    verification_status = models.CharField(max_length=20, choices=Verification.choices, default=Verification.PENDING)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ["-collection_date", "-created_at"]

    def save(self, *args, **kwargs):
        if self.activity_id and not self.project_id:
            self.project_id = self.activity.project_id
        super().save(*args, **kwargs)
